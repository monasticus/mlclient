"""The Init Env Command module.

It exports an implementation for 'init env' command:
    * InitEnvCommand
        Scaffolds an MLClient environment configuration file.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from cleo.commands.command import Command
from pydantic import ValidationError
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient import MLClient, MLEnvironment, constants
from mlclient.exceptions import EnvironmentFileExistsError, WrongParametersError

MANAGE_PORT = 8002
ADMIN_PORT = 8001

_SERVER_AUTH_TO_CLIENT = {
    "digest": "digest",
    "basic": "basic",
    "digestbasic": "digestbasic",
    "digest-basic": "digestbasic",
    "certificate": "certificate",
    "kerberos-ticket": "kerberos",
    "application-level": "digest",
}

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
  # app-services is the predefined default - shown for illustration, safe to remove.
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


class InitEnvCommand(Command):
    """Scaffolds an MLClient environment configuration file.

    Writes .mlclient/mlclient-<name>.yaml. Without a source option it emits a
    commented template; --from-gradle derives it from ml-gradle properties and
    --from-host derives it by querying a running MarkLogic instance.

    Usage:
      init env [options] [--] [<name>]

    Arguments:
      name
            The environment name. Omit to run the interactive wizard.

    Options:
      -i, --interactive
            Run the wizard even when a name is given
          --from-gradle=FROM-GRADLE
            Derive from ml-gradle properties (an env name or a file path)
          --from-host=FROM-HOST
            Derive by querying a MarkLogic host (host[:port])
      -u, --username=USERNAME
            Username for --from-host
      -p, --password=PASSWORD
            Password for --from-host (prompted if omitted)
      -g, --global
            Write to the home directory instead of the current directory
      -f, --force
            Overwrite an existing configuration file
    """

    name: str = "init env"
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
        ),
        option(
            "from-host",
            description="Derive by querying a MarkLogic host (host[:port])",
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
            description="Password for --from-host (prompted if omitted)",
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
        name = self.argument("name")
        if self.option("from-host"):
            if not name:
                msg = "--from-host requires an environment name"
                raise WrongParametersError(msg)
            content = self._render_from_host(name, self.option("from-host"))
            self._write_env_file(name, content)
            return 0
        if self.option("from-gradle"):
            if not name:
                msg = "--from-gradle requires an environment name"
                raise WrongParametersError(msg)
            content = self._render_from_gradle(self.option("from-gradle"))
            self._write_env_file(name, content)
            return 0
        if not name or self.option("interactive"):
            raise NotImplementedError
        self._write_env_file(name, _TEMPLATE)
        return 0

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

    def _render_from_host(
        self,
        app_name: str,
        spec: str,
    ) -> str:
        """Map a running MarkLogic's App Servers to an MLEnvironment YAML document.

        Connects to the host's Manage server, discovers its App Servers, and
        keeps those whose name matches ``app_name`` (all of them when nothing
        matches). Manage and Admin are emitted only when they diverge from the
        root connection; a matching pair is left for the client to derive.
        """
        host, port = _split_host_port(spec)
        username = self.option("username") or "admin"
        password = self.option("password") or self.secret("Password:")
        root = {
            "app-name": app_name,
            "protocol": "http",
            "host": host,
            "username": username,
            "password": password,
            "auth": "digest",
        }
        servers = self._discover_servers(host, port, username, password)
        env = _drop_none(
            {**root, "app-servers": _select_app_servers(servers, app_name, root)},
        )
        return yaml.safe_dump(env, sort_keys=False)

    def _discover_servers(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> list[dict]:
        """Read every HTTP App Server's connection detail from the Manage API."""
        # ponytail: http only; from-host over TLS needs a protocol/ssl flag.
        with MLClient(
            host=host,
            port=port,
            username=username,
            password=password,
        ) as ml:
            listing = ml.manage.servers.get_list(data_format="json").json()
            items = listing["server-default-list"]["list-items"]["list-item"]
            return [
                _server_details(ml, item)
                for item in items
                if item.get("kindref") == "http"
            ]

    def _render_from_gradle(
        self,
        selector: str,
    ) -> str:
        """Map ml-gradle properties to an MLEnvironment YAML document."""
        props = self._load_gradle_props(selector)
        env = _drop_none(
            {
                "app-name": props.get("mlAppName"),
                "protocol": _protocol(props, "ml"),
                "host": props.get("mlHost"),
                "username": props.get("mlUsername"),
                "password": props.get("mlPassword"),
                "auth": _lower(props.get("mlAuthentication")),
                "ssl": {"verify": False} if _has_simple_ssl(props) else None,
                "cloud": _cloud(props),
                "app-servers": _app_servers(props) or None,
            },
        )
        try:
            MLEnvironment(**env)
        except ValidationError as error:
            msg = (
                f"ml-gradle properties for [{selector}] do not form a valid "
                f"environment: {error}"
            )
            raise WrongParametersError(msg) from error
        return yaml.safe_dump(env, sort_keys=False) + _GRADLE_NA_HINTS

    def _load_gradle_props(
        self,
        selector: str,
    ) -> dict[str, str]:
        """Parse a gradle properties file, or merge base + gradle-<env> overlay."""
        path = Path(selector)
        if path.is_file():
            return _parse_properties(path)
        base = _parse_properties(Path.cwd() / "gradle.properties")
        base.update(_parse_properties(Path.cwd() / f"gradle-{selector}.properties"))
        if not base:
            msg = f"No ml-gradle properties found for [{selector}]"
            raise WrongParametersError(msg)
        return base


def _select_app_servers(
    servers: list[dict],
    app_name: str,
    root: dict,
) -> list[dict] | None:
    """Turn discovered servers into app-server entries.

    Servers whose name matches ``app_name`` become REST entries (all servers
    when nothing matches). The Manage and Admin tiers are emitted only when
    their protocol or auth diverges from the root connection.
    """
    matches = [
        server
        for server in servers
        if app_name.lower() in server["id"].lower()
    ] or servers
    entries = []
    for server in matches:
        if server["port"] in (MANAGE_PORT, ADMIN_PORT):
            tier = _tier_override(server, root)
            if tier:
                entries.append(tier)
        else:
            entries.append(_app_server_entry(server, root, rest=True))
    return entries or None


def _tier_override(
    server: dict,
    root: dict,
) -> dict | None:
    """Emit a Manage/Admin entry only when it diverges from the root connection."""
    tier_id = "manage" if server["port"] == MANAGE_PORT else "admin"
    entry = _app_server_entry(server, root, rest=False)
    entry["id"] = tier_id
    entry.pop("port")
    entry.pop("rest", None)
    return entry if set(entry) > {"id"} else None


def _app_server_entry(
    server: dict,
    root: dict,
    rest: bool,
) -> dict:
    """Build one app-server dict, omitting fields that match the root connection."""
    return _drop_none(
        {
            "id": server["id"],
            "port": server["port"],
            "rest": rest or None,
            "protocol": _diff(server["protocol"], root["protocol"]),
            "auth": _diff(server["auth"], root["auth"]),
        },
    )


def _server_details(
    ml: MLClient,
    item: dict,
) -> dict:
    """Read one App Server's port, protocol and client auth from its properties."""
    group = item["groupnameref"]
    props = ml.manage.servers.get_properties(
        item["nameref"],
        group,
        data_format="json",
    ).json()
    return {
        "id": props["server-name"],
        "port": props.get("port"),
        "protocol": "https" if props.get("ssl-certificate-template") else "http",
        "auth": _client_auth(props.get("authentication")),
    }


def _split_host_port(
    spec: str,
) -> tuple[str, int]:
    """Split a ``host[:port]`` spec, defaulting to the Manage port."""
    host, _, port = spec.partition(":")
    return host, int(port) if port else MANAGE_PORT


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
    """Build the app-servers list: REST always, others only when overridden.

    A server emits ``protocol`` only when its scheme / simple-SSL flags differ
    from the root connection; otherwise the model inherits the root protocol.
    Alongside protocol, only an explicit port, credential, or auth method makes
    a non-REST server worth emitting.
    """
    root_protocol = _protocol(props, "ml")
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
    others = (
        ("app-services", "mlAppServices"),
        ("manage", "mlManage"),
        ("admin", "mlAdmin"),
    )
    for server_id, prefix in others:
        keys = {
            "port": f"{prefix}Port",
            "username": f"{prefix}Username",
            "password": f"{prefix}Password",
            "auth": f"{prefix}Authentication",
        }
        server = _server(server_id, props, keys)
        _apply_server_protocol(server, props, prefix, root_protocol)
        if set(server) > {"id"}:
            servers.append(server)
    return servers


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
            "auth": _lower(props.get(keys["auth"])),
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


def _int(
    value: str | None,
) -> int | None:
    """Parse an int, tolerating None."""
    return int(value) if value is not None else None
