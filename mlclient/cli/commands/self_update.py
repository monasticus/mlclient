"""Upgrade MLClient and refresh existing agent integrations from the new package."""

from __future__ import annotations

import importlib.util
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from cleo.commands.command import Command
from cleo.helpers import option

from mlclient.cli.commands.install_skill import find_installed_skills
from mlclient.exceptions import WrongParametersError

# Exclude the working directory so project sources cannot shadow the upgraded wheel.
ENTRYPOINT = (
    "import sys; sys.path.pop(0); from mlclient.cli import main; sys.exit(main())"
)


class SelfUpdateCommand(Command):
    """Upgrade the running installation and its recorded agent integrations."""

    name = "self update"
    description = "Upgrade MLClient from PyPI and refresh installed skills"
    options = [option("dry-run", description="Show the update plan without changes")]

    def handle(self) -> int:
        """Run the package upgrade before invoking installers from the new version.

        Returns
        -------
        int
            Zero on success, or the failing updater/installer exit status.

        Raises
        ------
        WrongParametersError
            If a required package manager or installation configuration is invalid.
        OSError
            If a process cannot start or an installation cannot be inspected.
        """
        upgrade = _upgrade_command()
        records = find_installed_skills()
        self.line("Update MLClient from PyPI: " + shlex.join(upgrade))
        for record in records:
            scope = "user" if record["global"] else str(record["root"])
            self.line(f"Refresh skill for {record['agent']} ({scope})")
        if self.option("dry-run"):
            self.line("Dry run: no packages or files changed.")
            return 0
        result = subprocess.run(upgrade, check=False)
        if result.returncode:
            self.line_error(
                "Package upgrade failed; agent integrations were not changed.",
            )
            return result.returncode
        for record in records:
            args = [
                sys.executable,
                "-c",
                ENTRYPOINT,
                "install",
                "skill",
                record["agent"],
                "--force",
                "--no-interaction",
            ]
            if record["global"]:
                args.append("--global")
            result = subprocess.run(args, cwd=record["root"], check=False)
            if result.returncode:
                self.line_error(
                    "MLClient was upgraded, but an integration refresh failed. "
                    "Fix the reported error and rerun ml self update.",
                )
                return result.returncode
        self.line("MLClient updated. Restart the agent or start a new session.")
        return 0


def _upgrade_command() -> list[str]:
    """Select the owning package manager for the running installation.

    Returns
    -------
    list[str]
        Upgrade process arguments targeting the running installation.

    Raises
    ------
    WrongParametersError
        If the installation's package manager is unavailable.
    """
    prefix = Path(sys.prefix)
    if (prefix / "pipx_metadata.json").is_file():
        return [
            _required_executable("pipx"),
            "upgrade",
            "mlclient",
            "--pip-args=--index-url https://pypi.org/simple",
        ]
    if (prefix / "uv-receipt.toml").is_file():
        return [
            _required_executable("uv"),
            "tool",
            "upgrade",
            "mlclient",
            "--default-index",
            "https://pypi.org/simple",
        ]
    package = "mlclient"
    if importlib.util.find_spec("pip"):
        return [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            package,
            "--index-url",
            "https://pypi.org/simple",
        ]
    return [
        _required_executable("uv"),
        "pip",
        "install",
        "--upgrade",
        package,
        "--python",
        sys.executable,
        "--default-index",
        "https://pypi.org/simple",
    ]


def _required_executable(name: str) -> str:
    """Find a package manager or report why self-update cannot proceed.

    Parameters
    ----------
    name : str
        Package manager executable name.

    Returns
    -------
    str
        Executable path from the current PATH.

    Raises
    ------
    WrongParametersError
        If the executable is unavailable.
    """
    path = shutil.which(name)
    if path is None:
        message = f"Self-update requires {name} for this installation."
        raise WrongParametersError(message)
    return path
