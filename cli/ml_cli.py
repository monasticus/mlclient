"""The MLClient CLI module.

This module provides a Command Line Interface for ML Client.
It exports a single function:
    * main()
        Execute a MLCLIent Job using CLI.
"""

from __future__ import annotations

from cleo.application import Application

from mlclient import __version__ as ml_client_version


class MLCLIentApplication(Application):
    """An ML Client Command Line Application."""

    _APP_NAME = "MLCLIent"

    def __init__(
            self,
    ):
        """Initialize MLCLIentApplication instance."""
        super().__init__(self._APP_NAME, ml_client_version)

    @property
    def display_name(self) -> str:
        """The application name to display."""
        return self._name


def main() -> int:
    """Execute an ML Client Job using CLI."""
    return MLCLIentApplication().run()


if __name__ == "__main__":
    main()
