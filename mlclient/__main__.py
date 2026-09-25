"""The ML Client Main module.

This module executes cli:main() function.
"""

if __name__ == "__main__":
    import sys

    from mlclient.cli.app import main

    sys.exit(main())
