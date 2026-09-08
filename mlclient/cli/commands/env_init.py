"""The Env Init Command module.

It exports an implementation for 'env init' command:
    * EnvInitCommand
        Scaffolds an MLClient environment configuration file.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
from dataclasses import dataclass
from pathlib import Path
from textwrap import indent

import yaml
from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.io.io import IO
from cleo.ui.question import Question
from httpx import HTTPError
from pydantic import ValidationError

from mlclient import AsyncMLClient, MLEnvironment, constants
from mlclient.connection import SSLConfig
from mlclient.exceptions import EnvironmentFileExistsError, WrongParametersError
from mlclient.http_config import HTTPConfig

logger = logging.getLogger(__name__)

MANAGE_PORT = 8002
ADMIN_PORT = 8001
APP_SERVICES_PORT = 8000
HEALTH_PORT = 7997
MAX_PORT = 65535

_CLIENT_AUTH_METHODS = ("basic", "digest", "digestbasic")
_PROTOCOLS = ("http", "https")

_DEFAULT_SERVERS_BY_NAME = {
    "App-Services": ("app-services", APP_SERVICES_PORT, True),
    "Manage": ("manage", MANAGE_PORT, False),
    "Admin": ("admin", ADMIN_PORT, False),
    "HealthCheck": ("health", HEALTH_PORT, False),
}

_COMMENTED_APP_NAME = "# app-name: <optional; scopes discovery when set>\n"
_DEFAULT_SERVERS_SUMMARY = (
    "Defaults omitted unless overridden: app-services (8000, REST), "
    "manage (8002), admin (8001), health (7997, app).\n"
)
_DEFAULT_SERVERS_HINT = f"  # {_DEFAULT_SERVERS_SUMMARY}"

_SERVER_AUTH_TO_CLIENT = {
    "digest": "digest",
    "basic": "basic",
    "digestbasic": "digestbasic",
    "certificate": "certificate",
    "kerberos-ticket": "kerberos",
    "application-level": "app",
    "oauth": "oauth",
}

_UNSUPPORTED_SERVER_AUTH = ("saml",)

_TEMPLATE = """\
app-name: my-app

protocol: http
host: localhost
username: admin
password: admin
auth: digest

# ssl:
#   verify: true               # false, or a CA bundle path, for a self-signed cert
#   cert_file: /path/client.pem
#   key_file: /path/client.key
#   key_password: <passphrase>

# cloud:
#   api-key: <api-key>
#   base-path: /ml/instance/path
#   token-duration: 0

app-servers:
  # app-services is a predefined default - shown for illustration, safe to remove.
  - id: app-services
    port: 8000
    rest: true

  # A custom server inherits the root connection and auth above, overriding
  # only the fields it sets:
  # - id: my-rest-server
  #   port: 8010
  #   rest: true
  #   username: rest-user
  #   ssl:
  #     verify: false
"""

_GRADLE_NA_HINTS = """
# Not derivable from ml-gradle - uncomment and set if the connection needs them:
# ssl:
#   cert_file: /path/client.pem
#   key_file: /path/client.key
#   key_password: <passphrase>
# cloud:
#   token-duration: 0
"""


@dataclass
class _HostConnection:
    """Resolved --from-host connection details, ready for discovery."""

    name: str
    protocol: str
    host: str
    port: int
    username: str
    password: str
    auth: str


class _DefaultingSecretQuestion(Question):
    """Accept an empty hidden response as the configured default."""

    def _get_hidden_response(self, io: IO) -> str:
        """Avoid Cleo 2.1 reading a second line after an empty secret."""
        return super()._get_hidden_response(io) or self.default


class EnvInitCommand(Command):
    """Scaffolds an MLClient environment configuration file.

    Writes .mlclient/mlclient-<name>.yaml. Without a source option it emits a
    commented template; --from-gradle derives it from ml-gradle properties and
    --from-host derives it by querying a running MarkLogic instance.

    Usage:
      env init [options] [--] [<name>]

    Arguments:
      name
            The environment name. Omit to run the interactive wizard.

    Options:
      -i, --interactive
            Run the wizard even when a name is given
          --from-gradle[=FROM-GRADLE]
            Derive from ml-gradle properties (an env name or a file path)
          --from-host[=FROM-HOST]
            Derive by querying a MarkLogic host ([protocol://]host[:port])
          --app-name=APP-NAME
            Application label; scopes --from-host to matching servers
      -u, --username=USERNAME
            Username for --from-host
      -p, --password=PASSWORD
            Password for --from-host
      -a, --auth=AUTH
            Auth method for --from-host (basic, digest or digestbasic)
      -g, --global
            Write to the home directory instead of the current directory
      -f, --force
            Overwrite an existing configuration file
    """

    name: str = "env init"
    description: str = "Scaffolds an MLClient environment configuration file"
    arguments: list[Argument] = [
        argument(
            "name",
            "The environment name. Omit to run the interactive wizard.",
            optional=True,
        ),
    ]
    options: list[Option] = [
        option(
            "interactive",
            "i",
            description="Run the wizard even when a name is given",
        ),
        option(
            "from-gradle",
            description="Derive from ml-gradle properties (an env name or a file path)",
            flag=False,
            value_required=False,
        ),
        option(
            "from-host",
            description="Derive by querying a MarkLogic host ([protocol://]host[:port])",
            flag=False,
            value_required=False,
        ),
        option(
            "app-name",
            description="Application label; scopes --from-host to matching servers",
            flag=False,
        ),
        option(
            "username",
            "u",
            description="Username for --from-host",
            flag=False,
        ),
        option(
            "password",
            "p",
            description="Password for --from-host",
            flag=False,
        ),
        option(
            "auth",
            "a",
            description="Auth method for --from-host (basic, digest or digestbasic)",
            flag=False,
        ),
        option(
            "global",
            "g",
            description="Write to the home directory instead of the current directory",
        ),
        option(
            "force",
            "f",
            description="Overwrite an existing configuration file",
        ),
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        from_host = self._option_present("from-host")
        from_gradle = self._option_present("from-gradle")
        if from_host and from_gradle:
            msg = "Use only one of --from-host or --from-gradle, not both"
            raise WrongParametersError(msg)
        if from_host:
            return self._handle_from_host()
        if from_gradle:
            return self._handle_from_gradle()
        return self._handle_scaffold()

    def _option_present(
        self,
        option_name: str,
    ) -> bool:
        """Report whether an option token appeared, even without a value.

        ``self.option`` collapses an absent option and one passed without a value
        both to ``None``; only the raw input distinguishes them, which lets a bare
        ``--from-host`` use defaults or prompt when ``--interactive`` is set.
        """
        return self.io.input.has_parameter_option(f"--{option_name}", only_params=True)

    def _handle_scaffold(
        self,
    ) -> int:
        """Write the commented template, or run the wizard when no name is given."""
        name = self.argument("name")
        if name and not self.option("interactive"):
            self._write_env_file(name, _TEMPLATE)
            return 0
        return self._run_wizard(name)

    def _run_wizard(
        self,
        name: str | None,
    ) -> int:
        """Interactively scaffold an environment: pick a name, then a source mode.

        ``blank`` writes the commented template, ``gradle`` derives from ml-gradle
        properties (defaulting the selector to the name) and ``server`` discovers
        a running instance's App Servers.
        """
        name = name or self._ask_name()
        mode = self.choice("Source", ["blank", "gradle", "server"], 0)
        if mode == "gradle":
            selector = self._ask_gradle_selector(name)
            content = self._render_from_gradle(selector, _load_gradle_props(selector))
        elif mode == "server":
            content = self._render_from_host(
                self.option("app-name"),
                self._prompt_host_connection(name),
            )
        else:
            content = _TEMPLATE
        self._write_env_file(name, content)
        return 0

    def _prompt_host_connection(
        self,
        name: str,
    ) -> _HostConnection:
        """Prompt for the connection fields, defaulting to local-development values."""
        protocol, host, port, username, password = self._prompt_connection_fields(
            protocol=None,
            host=None,
            port=None,
            username=self.option("username"),
            password=self.option("password"),
        )
        return _HostConnection(
            name=name,
            protocol=protocol,
            host=host,
            port=port,
            username=username,
            password=password,
            auth=self._resolve_auth(prompt=True),
        )

    def _handle_from_host(
        self,
    ) -> int:
        """Resolve the host connection, discover its servers, then write."""
        conn = self._resolve_host_connection()
        content = self._render_from_host(self.option("app-name"), conn)
        self._write_env_file(conn.name, content)
        return 0

    def _resolve_host_connection(
        self,
    ) -> _HostConnection:
        """Merge command-line connection details with interactive prompts.

        A named invocation without ``--interactive`` resolves every omitted field
        to its local-development default. When the name is omitted or interactive
        mode is requested, only fields not supplied on the command line are asked.
        """
        spec = self.option("from-host")
        protocol, host, port = _parse_host_spec(spec) if spec else (None, None, None)
        name = self.argument("name")
        username = self.option("username")
        password = self.option("password")
        if name and not self.option("interactive"):
            return _HostConnection(
                name=name,
                protocol=protocol or "http",
                host=host or "localhost",
                port=port or MANAGE_PORT,
                username=username if username is not None else "admin",
                password=password if password is not None else "admin",
                auth=self._resolve_auth(),
            )

        name = name or self._ask_name()
        protocol, host, port, username, password = self._prompt_connection_fields(
            protocol=protocol,
            host=host,
            port=port,
            username=username,
            password=password,
        )
        return _HostConnection(
            name=name,
            protocol=protocol,
            host=host,
            port=port,
            username=username,
            password=password,
            auth=self._resolve_auth(prompt=True),
        )

    def _prompt_connection_fields(
        self,
        protocol: str | None,
        host: str | None,
        port: int | None,
        username: str | None,
        password: str | None,
    ) -> tuple[str, str, int, str, str]:
        """Prompt for missing connection fields with local-dev defaults."""
        protocol = protocol or self.choice("Protocol", list(_PROTOCOLS), 0)
        host = host or self.ask("Host [<comment>localhost</comment>]:", "localhost")
        port = port or self._ask_port()
        if username is None:
            username = self.ask("Username [<comment>admin</comment>]:", "admin")
        if password is None:
            password = self.secret(
                _DefaultingSecretQuestion(
                    "Password [<comment>admin</comment>]:",
                    "admin",
                ),
            )
        return protocol, host, port, username, password

    def _resolve_auth(
        self,
        prompt: bool = False,
    ) -> str:
        """Validate --auth, prompting for it when resolving interactively."""
        auth = self.option("auth")
        if auth is None:
            return (
                self.choice("Auth", list(_CLIENT_AUTH_METHODS), 1)
                if prompt
                else "digest"
            )
        if auth.lower() not in _CLIENT_AUTH_METHODS:
            msg = f"Unsupported auth method [{auth}]; use basic, digest or digestbasic"
            raise WrongParametersError(msg)
        return auth.lower()

    def _render_from_host(
        self,
        app_name: str | None,
        conn: _HostConnection,
    ) -> str:
        """Map a running MarkLogic's App Servers to an MLEnvironment YAML document.

        Connects to the host's Manage server and discovers its App Servers. When
        ``app_name`` is given it both labels the environment and keeps only the
        servers whose name matches it; when omitted every server is kept and the
        label is left commented out. Manage and Admin are emitted only when they
        diverge from the root connection; a matching pair is left for the client
        to derive.
        """
        root = {
            "protocol": conn.protocol,
            "host": conn.host,
            "username": conn.username,
            "password": conn.password,
            "auth": conn.auth,
            "ssl": _discovery_ssl(conn.protocol),
        }
        servers = self._discover_servers(conn)
        env = _drop_none(
            {
                **root,
                "app-servers": _select_app_servers(
                    servers,
                    app_name,
                    root,
                    _is_load_balancer(conn.host),
                ),
            },
        )
        return _render_env(app_name, env)

    def _discover_servers(
        self,
        conn: _HostConnection,
    ) -> list[dict]:
        """Read every HTTP App Server's connection detail from the Manage API."""
        url = f"{conn.protocol}://{conn.host}:{conn.port}"
        self.line(f"Connecting to <info>{url}</info>...")
        return asyncio.run(_read_servers(conn, url))

    def _handle_from_gradle(
        self,
    ) -> int:
        """Resolve the gradle selector and env name, prompting for what's missing."""
        selector = self.option("from-gradle")
        if selector:
            props = _load_gradle_props(selector)
            name = self._resolve_gradle_name(selector)
        else:
            name = self.argument("name") or self._ask_name()
            selector = self._ask_gradle_selector(name)
            props = _load_gradle_props(selector)
        content = self._render_from_gradle(selector, props)
        self._write_env_file(name, content)
        return 0

    def _resolve_gradle_name(
        self,
        selector: str,
    ) -> str:
        """Pick the environment name for a gradle selector.

        A name given on the command line wins. Otherwise a plain env-name
        selector doubles as the name, while a properties-file selector has no
        name to borrow and is prompted for; ``--interactive`` forces the prompt
        even for a derivable name, defaulting to the selector.
        """
        name = self.argument("name")
        if name:
            return name
        selector_is_file = _is_gradle_file_selector(selector)
        if not selector_is_file and not self.option("interactive"):
            return selector
        default = None if selector_is_file else selector
        return self._ask_name(default)

    def _render_from_gradle(
        self,
        selector: str,
        props: dict[str, str],
    ) -> str:
        """Map ml-gradle properties to an MLEnvironment YAML document."""
        app_name = props.get("mlAppName")
        env = _drop_none(
            {
                "protocol": _protocol(props, "ml"),
                "host": props.get("mlHost"),
                "username": props.get("mlUsername"),
                "password": props.get("mlPassword"),
                "auth": _config_auth(props.get("mlAuthentication")),
                "ssl": {"verify": False} if _has_simple_ssl(props) else None,
                "cloud": _cloud(props),
                "app-servers": _app_servers(props) or None,
            },
        )
        try:
            MLEnvironment(**{"app-name": app_name, **env})
        except ValidationError as error:
            msg = (
                f"ml-gradle properties for [{selector}] do not form a valid "
                f"environment: {error}"
            )
            raise WrongParametersError(msg) from error
        return _render_env(app_name, env) + _GRADLE_NA_HINTS

    def _write_env_file(
        self,
        name: str,
        content: str,
    ) -> None:
        """Write the environment file, refusing to clobber unless forced."""
        target = self._target_path(name)
        if target.exists() and not self.option("force"):
            raise EnvironmentFileExistsError(target.as_posix())
        target.parent.mkdir(exist_ok=True)
        target.write_text(content)
        self.line(f"Created <info>{target.as_posix()}</info>")

    def _target_path(
        self,
        name: str,
    ) -> Path:
        """Resolve the configuration file path in cwd, or home when --global."""
        base = Path.home() if self.option("global") else Path.cwd()
        return base / constants.ML_CLIENT_DIR / f"mlclient-{name}.yaml"

    def _ask_gradle_selector(
        self,
        name: str,
    ) -> str:
        """Prompt for a gradle env name or properties path, defaulting to the name."""
        prompt = (
            "Gradle environment name or properties file path "
            f"[<comment>{name}</comment>]:"
        )
        return self.ask(prompt, name)

    def _ask_name(
        self,
        default: str | None = None,
    ) -> str:
        """Prompt for an environment name, re-asking until it is non-empty."""
        question = Question("Environment name:", default)
        question.set_validator(_require_non_empty)
        question.set_max_attempts(5)
        return self.ask(question)

    def _ask_port(
        self,
    ) -> int:
        """Prompt for a port, re-asking until it is a valid port number."""
        question = Question("Port [<comment>8002</comment>]:", str(MANAGE_PORT))
        question.set_validator(_require_valid_port)
        question.set_max_attempts(5)
        return int(self.ask(question))


def _require_non_empty(
    value: str | None,
) -> str:
    """Reject a blank answer so an environment is never named after nothing."""
    if not value or not value.strip():
        msg = "Environment name must not be empty"
        raise ValueError(msg)
    return value.strip()


def _require_valid_port(
    value: str,
) -> str:
    """Reject an answer that is not a port number in the 1-65535 range."""
    if not str(value).isdigit() or not 1 <= int(value) <= MAX_PORT:
        msg = "Port must be a whole number between 1 and 65535"
        raise ValueError(msg)
    return value


def _render_env(
    app_name: str | None,
    env: dict,
) -> str:
    """Serialize the environment, commenting out the app-name label when unset."""
    data = {"app-name": app_name, **env} if app_name else dict(env)
    servers = data.pop("app-servers", None)
    content = yaml.safe_dump(data, sort_keys=False)
    if servers:
        content += "app-servers:\n" + _DEFAULT_SERVERS_HINT
        content += indent(yaml.safe_dump(servers, sort_keys=False), "  ")
    else:
        content += f"\n# app-servers:\n#   {_DEFAULT_SERVERS_SUMMARY}"
    return ("" if app_name else _COMMENTED_APP_NAME) + content


def _select_app_servers(
    servers: list[dict],
    app_name: str | None,
    root: dict,
    is_load_balancer: bool,
) -> list[dict] | None:
    """Turn discovered servers into app-server entries.

    When ``app_name`` is given, only matching servers are kept (all servers when
    nothing matches); without it every server is kept. A predefined default is
    emitted only when it diverges from what the loaded environment already
    provides: behind a load balancer only a divergent port or REST flag counts,
    because the balancer terminates the connection and every server is reached with
    the root protocol and auth; a directly reached host also compares protocol and
    auth. A default matching on every compared field is left out entirely.
    """
    matches = servers
    if app_name:
        matches = [
            server for server in servers if app_name.lower() in server["id"].lower()
        ] or servers
    entries = [_app_server_entry(server, root, is_load_balancer) for server in matches]
    return [entry for entry in entries if entry] or None


def _app_server_entry(
    server: dict,
    root: dict,
    is_load_balancer: bool,
) -> dict | None:
    """Build one app-server entry, or None when a default matches the environment.

    A predefined default is matched by its MarkLogic name so a relocated one keeps
    its canonical id and replaces the predefined entry instead of adding a
    duplicate; anything else is a custom server that is always recorded.
    """
    default = _DEFAULT_SERVERS_BY_NAME.get(server["id"])
    if default is None:
        return _custom_server_entry(server, root, is_load_balancer)
    return _default_server_entry(server, default, root, is_load_balancer)


def _default_server_entry(
    server: dict,
    default: tuple[str, int, bool],
    root: dict,
    is_load_balancer: bool,
) -> dict | None:
    """Emit a lowercase default-server override only when it diverges.

    A load-balanced host compares only port and REST; a directly reached one also
    compares protocol and auth. Because an emitted entry replaces the predefined
    default and inherits nothing from it, every field needed to reproduce the
    server is restated - the port unless it is the connection default, the REST
    flag whenever it is set or diverges, and health's own auth which never matches
    the root.
    """
    server_id, standard_port, default_rest = default
    expected_auth = "app" if server_id == "health" else root["auth"]
    port_diverges = server["port"] != standard_port
    rest_diverges = server["rest"] != default_rest
    protocol_diverges = not is_load_balancer and server["protocol"] != root["protocol"]
    auth_diverges = not is_load_balancer and server["auth"] != expected_auth
    if not (port_diverges or rest_diverges or protocol_diverges or auth_diverges):
        return None
    entry = {"id": server_id}
    if server["port"] != APP_SERVICES_PORT:
        entry["port"] = server["port"]
    if server["rest"] or rest_diverges:
        entry["rest"] = server["rest"]
    if protocol_diverges:
        entry["protocol"] = server["protocol"]
    if auth_diverges or server_id == "health":
        entry["auth"] = server["auth"]
    return entry


def _custom_server_entry(
    server: dict,
    root: dict,
    is_load_balancer: bool,
) -> dict:
    """Build one entry for a server with no predefined default, always recorded."""
    entry = {"id": server["id"], "port": server["port"]}
    if server["rest"]:
        entry["rest"] = True
    if not is_load_balancer:
        _record_divergent_connection(entry, server, root)
    return entry


def _record_divergent_connection(
    entry: dict,
    server: dict,
    root: dict,
) -> None:
    """Record a server's protocol and auth when they differ from the root."""
    protocol = _diff(server["protocol"], root["protocol"])
    if protocol is not None:
        entry["protocol"] = protocol
    auth = _diff(server["auth"], root["auth"])
    if auth is not None:
        entry["auth"] = auth


async def _read_servers(
    conn: _HostConnection,
    url: str,
) -> list[dict]:
    """Fetch every HTTP App Server's detail concurrently over the Manage API."""
    ssl = _discovery_ssl(conn.protocol)
    manage_config = HTTPConfig.resolve(
        protocol=conn.protocol,
        host=conn.host,
        port=conn.port,
        username=conn.username,
        password=conn.password,
        auth=conn.auth,
        ssl=SSLConfig(**ssl) if ssl else None,
    )
    async with AsyncMLClient(manage_config=manage_config) as ml:
        listing = await _read_server_listing(ml, url)
        items = listing["server-default-list"]["list-items"]["list-item"]
        details = await asyncio.gather(
            *(
                _server_details(ml, item)
                for item in items
                if item.get("kindref") == "http"
            ),
        )
        return [server for server in details if server is not None]


async def _server_details(
    ml: AsyncMLClient,
    item: dict,
) -> dict | None:
    """Read one App Server's connection detail, or skip it when unsupported.

    A server whose authentication scheme has no MLClient equivalent (e.g. SAML)
    cannot be reproduced, so it is dropped with a warning rather than emitted
    with a substitute auth that would silently connect the wrong way.
    """
    group = item["groupnameref"]
    props = (
        await ml.manage.servers.get_properties(
            item["nameref"],
            group,
            data_format="json",
        )
    ).json()
    server_name = props["server-name"]
    auth = props.get("authentication")
    if auth is not None and auth.lower() in _UNSUPPORTED_SERVER_AUTH:
        logger.warning(
            "Skipping App Server %r: its %r authentication has no MLClient equivalent.",
            server_name,
            auth.lower(),
        )
        return None
    return {
        "id": server_name,
        "port": props.get("port"),
        "rest": str(props.get("url-rewriter", "")).startswith(
            "/MarkLogic/rest-api/",
        ),
        "protocol": "https" if props.get("ssl-certificate-template") else "http",
        "auth": _client_auth(auth),
    }


async def _read_server_listing(
    ml: AsyncMLClient,
    url: str,
) -> dict:
    """Fetch and parse the Manage server listing, or explain why it failed.

    The listing is discovered over a raw response, so an unreachable host, a
    wrong port, a TLS-only server answering plain http, or bad credentials each
    surface differently - a transport error, an error status, or a non-JSON
    body. Left to the caller, the last two collapse into a cryptic
    ``Expecting value`` JSONDecodeError, so each is turned into a
    connection-failure message that names the endpoint and its status.
    """
    try:
        response = await ml.manage.servers.get_list(data_format="json")
    except HTTPError as error:
        msg = f"Could not connect to {url}: {error}"
        raise WrongParametersError(msg) from error
    if not response.is_success:
        msg = (
            f"Could not read the App Server listing from {url}: "
            f"HTTP {response.status_code} {response.reason_phrase}."
        )
        raise WrongParametersError(msg)
    try:
        return response.json()
    except ValueError as error:
        msg = (
            f"Could not read the App Server listing from {url}: the response "
            f"was not valid JSON (HTTP {response.status_code})."
        )
        raise WrongParametersError(msg) from error


def _is_load_balancer(
    host: str,
) -> bool:
    """Treat any non-local hostname as sitting behind a load balancer.

    ``localhost`` and bare IP addresses reach a MarkLogic host directly, so each
    App Server's own protocol and authentication are reproducible. Any other name
    resolves through a balancer that terminates the connection, so the client
    reaches every server with the root protocol and auth - the servers' own
    listener settings would only misdirect a reloaded environment.
    """
    if host == "localhost":
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return True
    return False


def _discovery_ssl(
    protocol: str,
) -> dict | None:
    """SSL settings for talking to a discovered host, recorded in the env too.

    Dev MarkLogic serves self-signed certificates, so verification is disabled for
    an ``https`` connection and written into the generated file so it loads the
    same way. Point ``ssl.verify`` at a CA bundle when the host has a trusted cert.
    """
    return {"verify": False} if protocol == "https" else None


def _parse_host_spec(
    spec: str,
) -> tuple[str | None, str, int | None]:
    """Split a ``[protocol://]host[:port]`` spec; protocol/port are None when absent."""
    protocol = None
    if "://" in spec:
        scheme, _, spec = spec.partition("://")
        if scheme.lower() not in _PROTOCOLS:
            msg = f"Unsupported protocol [{scheme}]; use http or https"
            raise WrongParametersError(msg)
        protocol = scheme.lower()
    host, _, port = spec.partition(":")
    if not host:
        msg = "--from-host requires a host name"
        raise WrongParametersError(msg)
    try:
        return protocol, host, int(_require_valid_port(port)) if port else None
    except ValueError as error:
        raise WrongParametersError(str(error)) from error


def _client_auth(
    server_auth: str | None,
) -> str:
    """Map a server's authentication scheme to a client auth method."""
    if server_auth is None:
        return "digest"
    return _SERVER_AUTH_TO_CLIENT.get(server_auth.lower(), "digest")


def _diff(
    value: str | None,
    root_value: str | None,
) -> str | None:
    """Return the value only when it differs from the root's, else None."""
    return value if value != root_value else None


def _app_servers(
    props: dict[str, str],
) -> list[dict]:
    """Build the app-servers list, keeping only divergent entries.

    The dedicated REST server is always emitted; a predefined default only when it
    diverges from what the loaded environment already provides.
    A server emits ``protocol`` only when its scheme / simple-SSL flags differ from
    the root connection. A predefined default (app-services, manage, admin) is left
    out entirely when its port is the standard one and no protocol, credential or
    auth diverges; when it is emitted the standard port stays implicit and only
    app-services restates its REST flag, which the replacing entry would otherwise
    lose.
    """
    root_protocol = _protocol(props, "ml")
    root_auth = _config_auth(props.get("mlAuthentication")) or "digest"
    servers = []
    if props.get("mlRestPort"):
        rest_keys = {
            "port": "mlRestPort",
            "username": "mlRestAdminUsername",
            "password": "mlRestAdminPassword",
            "auth": "mlRestAuthentication",
        }
        server = _server("rest", props, rest_keys, rest=True)
        _apply_server_protocol(server, props, "mlRest", root_protocol)
        servers.append(server)
    defaults = (
        ("app-services", "mlAppServices", APP_SERVICES_PORT),
        ("manage", "mlManage", MANAGE_PORT),
        ("admin", "mlAdmin", ADMIN_PORT),
    )
    for server_id, prefix, standard_port in defaults:
        keys = {
            "port": f"{prefix}Port",
            "username": f"{prefix}Username",
            "password": f"{prefix}Password",
            "auth": f"{prefix}Authentication",
        }
        server = _server(server_id, props, keys)
        _apply_server_protocol(server, props, prefix, root_protocol)
        entry = _default_gradle_entry(server, standard_port, root_auth)
        if entry:
            servers.append(entry)
    return servers


def _default_gradle_entry(
    server: dict,
    standard_port: int,
    root_auth: str,
) -> dict | None:
    """Reduce a default server to the fields that diverge, or None when it matches.

    Only genuine app-server settings are compared - port, protocol and auth; the
    standard port is implicit (omitted unless relocated), auth is dropped when it
    equals the root's, and app-services always restates ``rest: true`` because the
    entry replaces the predefined default rather than merging onto it.
    """
    port = server.get("port")
    auth = server.get("auth")
    diverges = (
        (port is not None and port != standard_port)
        or "protocol" in server
        or (auth is not None and auth != root_auth)
    )
    if not diverges:
        return None
    entry = {"id": server["id"]}
    if port is not None and port != APP_SERVICES_PORT:
        entry["port"] = port
    if "protocol" in server:
        entry["protocol"] = server["protocol"]
    if auth is not None and auth != root_auth:
        entry["auth"] = auth
    if server["id"] == "app-services":
        entry["rest"] = True
    return entry


def _apply_server_protocol(
    server: dict,
    props: dict[str, str],
    prefix: str,
    root_protocol: str | None,
) -> None:
    """Set a server's protocol when it differs from the root connection's."""
    protocol = _protocol(props, prefix)
    if protocol is not None and protocol != (root_protocol or "http"):
        server["protocol"] = protocol


def _server(
    server_id: str,
    props: dict[str, str],
    keys: dict[str, str],
    rest: bool = False,
) -> dict:
    """Build one app-server dict from its ml-gradle per-connection properties."""
    return _drop_none(
        {
            "id": server_id,
            "port": _int(props.get(keys["port"])),
            "rest": rest or None,
            "username": props.get(keys["username"]),
            "password": props.get(keys["password"]),
            "auth": _config_auth(props.get(keys["auth"])),
        },
    )


def _cloud(
    props: dict[str, str],
) -> dict | None:
    """Build the cloud block from ml-gradle cloud properties, if any are set."""
    cloud = _drop_none(
        {
            "api-key": props.get("mlCloudApiKey"),
            "base-path": props.get("mlCloudBasePath"),
        },
    )
    return cloud or None


def _protocol(
    props: dict[str, str],
    prefix: str,
) -> str | None:
    """Resolve a connection's protocol from its scheme / simple-SSL flags.

    Returns None when neither is set, so the connection inherits its protocol.
    """
    scheme = _lower(props.get(f"{prefix}Scheme"))
    simple_ssl = _lower(props.get(f"{prefix}SimpleSsl"))
    if scheme == "https" or simple_ssl == "true":
        return "https"
    if scheme == "http" or simple_ssl == "false":
        return "http"
    return None


def _has_simple_ssl(
    props: dict[str, str],
) -> bool:
    """Detect any ml-gradle simple-SSL flag."""
    return any(
        key.endswith("SimpleSsl") and _lower(value) == "true"
        for key, value in props.items()
    )


def _load_gradle_props(
    selector: str,
) -> dict[str, str]:
    """Read ml-gradle properties for a file-path selector or a profile name.

    A ``.properties`` selector is a file path: it is parsed on its own when it
    exists, otherwise the command lists the profiles living beside it. A plain
    name is a profile: ``gradle-<name>.properties`` in the current directory,
    merged over ``gradle.properties``; a missing profile lists the available
    ones.
    """
    if _is_gradle_file_selector(selector):
        path = Path(selector)
        if path.is_file():
            return _parse_properties(path)
        raise WrongParametersError(_missing_gradle_file_message(path))
    overlay = Path.cwd() / f"gradle-{selector}.properties"
    if not overlay.is_file():
        raise WrongParametersError(_unknown_gradle_profile_message(selector))
    props = _parse_properties(Path.cwd() / "gradle.properties")
    props.update(_parse_properties(overlay))
    return props


def _is_gradle_file_selector(
    selector: str,
) -> bool:
    """Tell a file-path selector from a profile name; a path ends in .properties."""
    return selector.endswith(".properties")


def _missing_gradle_file_message(
    path: Path,
) -> str:
    """Report the missing file, listing the .properties files beside it."""
    directory = path.parent
    files = sorted(sibling.name for sibling in directory.glob("*.properties"))
    location = "" if directory == Path() else f" in {directory}"
    available = f" Files{location}: {', '.join(files)}." if files else ""
    return f"No properties file at [{path}].{available}"


def _unknown_gradle_profile_message(
    selector: str,
) -> str:
    """Report the unknown profile, listing the profiles present in the cwd."""
    profiles = sorted(
        path.name.removeprefix("gradle-").removesuffix(".properties")
        for path in Path.cwd().glob("gradle-*.properties")
    )
    available = f" Available profiles: {', '.join(profiles)}." if profiles else ""
    return f"No ml-gradle properties found for [{selector}].{available}"


def _parse_properties(
    path: Path,
) -> dict[str, str]:
    """Read a Java .properties file into a dict, skipping blanks and comments."""
    if not path.is_file():
        return {}
    props = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "!")) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


def _drop_none(
    mapping: dict,
) -> dict:
    """Return the mapping without keys whose value is None."""
    return {key: value for key, value in mapping.items() if value is not None}


def _lower(
    value: str | None,
) -> str | None:
    """Lowercase a value, tolerating None."""
    return value.lower() if value is not None else None


def _config_auth(
    value: str | None,
) -> str | None:
    """Map an ml-gradle server auth name to the environment spelling."""
    if value is None:
        return None
    auth = value.lower()
    return _SERVER_AUTH_TO_CLIENT.get(auth, auth)


def _int(
    value: str | None,
) -> int | None:
    """Parse an int, tolerating None."""
    return int(value) if value is not None else None
