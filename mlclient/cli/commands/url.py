"""The URL Command module.

It exports an implementation for 'url' command:
    * UrlCommand
        Prints MarkLogic browser URLs for an environment.
"""

from __future__ import annotations

import subprocess
import webbrowser

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.ui.table import Table

from mlclient.cli.clipboard import copy_to_clipboard
from mlclient.env import MLEnvironment
from mlclient.exceptions import WrongParametersError

_TARGETS = {
    "admin": ("Admin UI", "admin", ""),
    "qconsole": ("QConsole", "app-services", "/qconsole"),
    "qc": ("QConsole", "app-services", "/qconsole"),
    "manage": ("Monitoring Dashboard", "manage", "/dashboard"),
    "monitoring": ("Monitoring Dashboard", "manage", "/dashboard"),
}

_BASIC_TARGETS = ("qconsole", "admin", "monitoring")


class UrlCommand(Command):
    """Prints MarkLogic browser URLs for an environment.

    With no target it prints the QConsole, Admin UI and Monitoring Dashboard
    URLs. With a target it prints that one URL and copies it to the clipboard;
    with ``--open`` it prints the URL and opens it in the default browser
    instead of copying. A target that is not a known alias is treated as an App
    Server id.

    Usage:
      url [options] [--] [<target>]

    Arguments:
      target
            admin, qconsole (qc), manage, monitoring, or an App Server id.
            Omit to print the QConsole, Admin UI and Monitoring Dashboard URLs.

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
          --open
            Open the URL in the default browser instead of copying it
    """

    name: str = "url"
    description: str = "Prints MarkLogic browser URLs for an environment"
    arguments: list[Argument] = [
        argument(
            "target",
            "admin, qconsole (qc), manage, monitoring, or an App Server id.",
            optional=True,
        ),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
        ),
        option(
            "open",
            description="Open the URL in the default browser instead of copying it",
        ),
    ]

    def handle(self) -> int:
        """Execute the command."""
        env_name = self.option("environment")
        env = MLEnvironment.load(env_name)
        target = self.argument("target")
        if not target:
            return self._print_basics(env, env_name)
        return self._print_target(env, env_name, target)

    def _print_basics(self, env: MLEnvironment, env_name: str) -> int:
        """Render the QConsole, Admin UI and Monitoring Dashboard URLs."""
        if self.option("open"):
            msg = "Specify a target to open in the browser."
            raise WrongParametersError(msg)
        self._render(env_name, [_resolve(env, target) for target in _BASIC_TARGETS])
        return 0

    def _print_target(self, env: MLEnvironment, env_name: str, target: str) -> int:
        """Render one labelled URL, then open it in the browser or copy it."""
        label, url = _resolve(env, target)
        self._render(env_name, [(label, url)])
        if self.option("open"):
            webbrowser.open(url)
            self.line("Opened in browser.", style="fg=green;options=italic")
            return 0
        self._copy(url)
        return 0

    def _render(self, env_name: str, rows: list[tuple[str, str]]) -> None:
        """Render label/URL rows in a titled box.

        cleo draws the box's top border only for a header row, so the header is
        required; without it the top border degrades to a row separator.
        """
        table = Table(self.io, style="box")
        table.set_headers(["Interface", "URL"])
        table.set_header_title(f" {env_name} ")
        for label, url in rows:
            table.add_row([f"<fg=cyan;options=bold>{label}</>", f"<info>{url}</info>"])
        table.render()

    def _copy(self, url: str) -> None:
        """Copy the URL to the clipboard, keeping clipboard failures non-fatal."""
        try:
            copy_to_clipboard(url)
        except (OSError, subprocess.SubprocessError):
            self.line_error(
                "Could not copy to clipboard. Check that a clipboard "
                "tool and a desktop session are available.",
                style="fg=yellow;options=dark",
            )
            return
        self.line("Copied to clipboard.", style="fg=green;options=italic")


def _resolve(env: MLEnvironment, target: str) -> tuple[str, str]:
    """Resolve a target to its display label and protocol://host:port URL."""
    label, app_server_id, path = _TARGETS.get(target, (target, target, ""))
    config = env.provide_config_dict(app_server_id)
    url = f"{config['protocol']}://{config['host']}:{config['port']}{path}"
    return label, url
