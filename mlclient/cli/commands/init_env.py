"""The Init Env Command module.

It exports an implementation for 'init env' command:
    * InitEnvCommand
        Scaffolds an MLClient environment configuration file.
"""

from __future__ import annotations

from pathlib import Path

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient import constants
from mlclient.exceptions import EnvironmentFileExistsError

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
        if self.option("from-gradle") or self.option("from-host"):
            raise NotImplementedError
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
