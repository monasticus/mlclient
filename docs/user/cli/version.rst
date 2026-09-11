version
=======

.. code-block:: none

    Description:
      Reports the MarkLogic version of an environment

    Usage:
      version [options]

    Options:
      -e, --environment=ENVIRONMENT  The ML Client environment name [default: "local"]
      -c, --connection=CONNECTION  Connection identifier from the environment or TCP port

      -h, --help                     Display help for the given command. When no command is given display help for the list command.
      -q, --quiet                    Do not output any message.
      -V, --version                  Display this application version.
          --ansi                     Force ANSI output.
          --no-ansi                  Disable ANSI output.
      -n, --no-interaction           Do not ask any interactive question.
      -v|vv|vvv, --verbose           Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.

The command resolves the MarkLogic version through the environment's REST
server (see :doc:`../setup`) and prints the complete original version,
e.g. ``12.0.1`` or ``10.0-9.5``.

The version comes from ``xdmp:version()``. When the connecting user lacks the
eval privilege, the Manage and Admin server-config endpoints are tried in turn;
unavailable endpoints and malformed fallback responses are skipped. If none
succeeds the original eval error is raised.


Report the version
------------------

.. code-block:: bash

    ml version

Pass ``--connection`` (``-c``) to select a specific REST App-Server id from the
environment instead of the default:

.. code-block:: bash

    ml version -c content

All version components, separators and suffixes are preserved. An invalid eval
version makes the command fail with an error.

``-c / --connection`` accepts an environment connection identifier or a TCP
port (1-65535). A port overrides the default REST connection port, retaining
its other settings. Omit it to use the default REST connection.
