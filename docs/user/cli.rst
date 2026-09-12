Command Line Interface
======================

MLClient provides you a nice command line interface using `cleo <https://github.com/python-poetry/cleo>`_ library.

.. code-block:: none

    MLCLIent (version 0.4.0)

    Usage:
      command [options] [arguments]

    Options:
      -h, --help            Display help for the given command. When no command is given display help for the list command.
      -q, --quiet           Do not output any message.
      -V, --version         Display this application version.
          --ansi            Force ANSI output.
          --no-ansi         Disable ANSI output.
      -n, --no-interaction  Do not ask any interactive question.
      -v|vv|vvv, --verbose  Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.

    Available commands:
      eval       Sends a POST request to the /v1/eval endpoint
      health     Reports whether a MarkLogic environment's HealthCheck server is up
      help       Displays help for a command.
      http       Sends a raw HTTP request to any REST endpoint
      list       Lists commands.
      log-level  Shows or sets a MarkLogic file/system log level
      logs       Sends a GET request to the /manage/v2/logs endpoint
      version    Reports the MarkLogic version of an environment

     env
      env init   Scaffolds an MLClient environment configuration file
      env show   Lists MLClient environments, or renders one environment's settings

The former ``call eval`` and ``call logs`` commands are now ``eval`` and
``logs``. Use ``http`` for raw requests to other REST endpoints.

Connection and target selection
-------------------------------

``http``, ``eval``, ``version`` and ``log-level`` use ``-c / --connection``
to select a configured connection identifier or a TCP port. A numeric port
changes the default REST connection's port and retains its other settings.

``logs -s / --server`` selects whose logs to read by an environment identifier
or port. ``log-level -s / --server`` instead takes the actual App Server name
in MarkLogic. It does not select the connection used for the request.

Server commands default to the ``local`` environment; ``-e / --environment``
selects another environment. These connection options replace the former
``-s / --rest-server``; ``logs --server`` replaces ``--app-server``.

.. caution::

    All MLClient commands use MLClient Environment. To set it up, see :doc:`./setup`.

.. toctree::
   :hidden:

   cli/eval
   cli/logs
   cli/http
   cli/health
   cli/log-level
   cli/version
   cli/env


Log-level diagnostics are available with ``ml log-level -vv``. Debug messages
show the eval attempt (which runs the Admin module), authorization failures
that trigger Manage REST fallback, and the result or reason for failure.
There is no separate Admin REST fallback.
