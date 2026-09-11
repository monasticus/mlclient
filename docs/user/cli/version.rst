version
=======

.. code-block:: none

    Description:
      Reports the MarkLogic version of an environment

    Usage:
      version [options]

    Options:
      -e, --environment=ENVIRONMENT  The ML Client environment name [default: "local"]
      -s, --rest-server=REST-SERVER  The ML REST Server environmental id

      -h, --help                     Display help for the given command. When no command is given display help for the list command.
      -q, --quiet                    Do not output any message.
      -V, --version                  Display this application version.
          --ansi                     Force ANSI output.
          --no-ansi                  Disable ANSI output.
      -n, --no-interaction           Do not ask any interactive question.
      -v|vv|vvv, --verbose           Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.

The command resolves the MarkLogic version through the environment's REST
server (see :doc:`../setup`) and prints it in dotted form, e.g. ``12.0.1``.

The version comes from ``xdmp:version()``. When the connecting user lacks the
eval privilege, the Manage and Admin server-config endpoints are tried in turn;
unavailable endpoints and malformed fallback responses are skipped. If none
succeeds the original eval error is raised.


Report the version
------------------

.. code-block:: bash

    ml version -e local

Pass ``--rest-server`` (``-s``) to select a specific REST App-Server id from the
environment instead of the default:

.. code-block:: bash

    ml version -e local -s content

Versions such as ``10.0-9.5`` are printed as ``10.0.9``. Build and hotfix
suffixes are excluded; a missing patch defaults to zero. An invalid eval
version makes the command fail with an error.
