"""The ML Client CLI package.

It contains modules providing Command Line Interface for ML Client App:
    * ml_cli
        The MLClient CLI module.

It exports a single function:
    * main()
        Execute a MLCLIent Job using CLI.
"""
from .app import main

__all__ = ["main"]
