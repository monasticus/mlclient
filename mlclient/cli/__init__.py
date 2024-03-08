"""The ML Client CLI package.

It contains modules providing Command Line Interface for ML Client App:
    * app
        The MLClient CLI module.

It exports a single function and a single class:
    * main()
        Run an MLCLIent Application.
    * MLCLIentApplication
        An ML Client Command Line Cleo Application.
"""

from .app import MLCLIentApplication, main

__all__ = ["MLCLIentApplication", "main"]
