"""The ML Client CLI package.

It contains modules providing Command Line Interface for ML Client App:
    * app
        The MLClient CLI module.

It exports a single function:
    * main()
        Run an MLCLIent Application.
"""
from .app import main

__all__ = ["main"]
