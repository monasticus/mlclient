"""The MLClient CLI module.

This module provides a Command Line Interface for ML Client.
It exports a single function:
    * main()
        Execute a MLCLIent Job.
"""
from __future__ import annotations

from argparse import ArgumentParser, Namespace


def main():
    """Execute a Mimeo Job using CLI."""
    MLCLIentJob()


class MLCLIentJob:
    """A class representing a single ML Client CLI job."""

    def __init__(
            self,
    ):
        """Initialize MLCLIent instance."""
        self._args: Namespace = MLCLIentArgumentParser().parse_args()


class MLCLIentArgumentParser(ArgumentParser):
    """A custom ArgumentParser for the ML Client CLI."""

    def __init__(self):
        """Initialize MLCLIentArgumentParser instance."""
        super().__init__(
            prog="ml",
            description="Manage your MarkLogic instance with ease")
        self._add_positional_arguments()

    def _add_positional_arguments(
            self,
    ):
        """Add positional arguments."""
        self.add_argument(
            "-v",
            "--version",
            action="version",
            version="MLClient v0.1.0")


if __name__ == "__main__":
    main()
