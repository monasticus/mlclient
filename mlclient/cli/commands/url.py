"""The URL Command module.

It exports an implementation for 'url' command:
    * UrlCommand
        Prints MarkLogic browser URLs for an environment.
"""

from __future__ import annotations

import subprocess
import webbrowser

from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.ui.table import Table

from mlclient.cli.clipboard import copy_to_clipboard
from mlclient.cli.commands._multi_env_common import selected_environments
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
    Server id. With several environments the table has a URL column per
    environment; a target copies all of its URLs, one per line, or opens each.

    Usage:
      url [options] [--] [<target>]

    Arguments:
      target
            admin, qconsole (qc), manage, monitoring, or an App Server id.
            Omit to print the QConsole, Admin UI and Monitoring Dashboard URLs.

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name; repeat it to show several
            environments (multiple values allowed) [default: ["local"]]
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
            description="The ML Client environment name; repeat it to show "
            "several environments",
            flag=False,
            multiple=True,
            default=["local"],
        ),
        option(
            "open",
            description="Open the URL in the default browser instead of copying it",
        ),
    ]

    def handle(self) -> int:
        """Execute the command."""
        envs = {name: MLEnvironment.load(name) for name in selected_environments(self)}
        target = self.argument("target")
        if not target:
            return self._print_basics(envs)
        return self._print_target(envs, target)

    def _print_basics(self, envs: dict[str, MLEnvironment]) -> int:
        """Render the QConsole, Admin UI and Monitoring Dashboard URLs."""
        if self.option("open"):
            msg = "Specify a target to open in the browser."
            raise WrongParametersError(msg)
        self._render(list(envs), [_resolve(envs, target) for target in _BASIC_TARGETS])
        return 0

    def _print_target(self, envs: dict[str, MLEnvironment], target: str) -> int:
        """Render one labelled row of URLs, then open them or copy them."""
        label, urls = _resolve(envs, target)
        self._render(list(envs), [(label, urls)])
        if self.option("open"):
            return max([self._open(url) for url in urls])
        self._copy("\n".join(urls))
        return 0

    def _open(self, url: str) -> int:
        """Open a URL, reporting when no browser accepts the request."""
        try:
            opened = webbrowser.open(url)
        except webbrowser.Error:
            opened = False
        if opened:
            self.line("Opened in browser.", style="fg=green;options=italic")
            return 0
        self.line_error(
            "Could not open a browser. Open the printed URL manually.",
            style="fg=yellow;options=dark",
        )
        return 1

    def _render(self, env_names: list[str], rows: list[tuple[str, list[str]]]) -> None:
        """Render label/URL rows in a box, one URL column per environment.

        A single environment names the box and heads its column "URL"; several
        head their columns with the environment names. cleo draws the box's top
        border only for a header row, so the header is required; without it the
        top border degrades to a row separator.
        """
        table = Table(self.io, style="box")
        if len(env_names) == 1:
            table.set_headers(["Interface", "URL"])
            table.set_header_title(f" {Formatter.escape(env_names[0])} ")
        else:
            table.set_headers(["Interface", *map(Formatter.escape, env_names)])
        for label, urls in rows:
            table.add_row(
                [
                    f"<fg=cyan;options=bold>{Formatter.escape(label)}</>",
                    *(f"<info>{Formatter.escape(url)}</info>" for url in urls),
                ],
            )
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


def _resolve(envs: dict[str, MLEnvironment], target: str) -> tuple[str, list[str]]:
    """Resolve a target to its display label and each protocol://host:port URL."""
    label, app_server_id, path = _TARGETS.get(target, (target, target, ""))
    urls = []
    for env in envs.values():
        config = env.provide_config_dict(app_server_id)
        urls.append(f"{config['protocol']}://{config['host']}:{config['port']}{path}")
    return label, urls
