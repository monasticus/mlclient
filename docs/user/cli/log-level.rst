log-level
=========

.. code-block:: none

    Description:
      Shows or sets a MarkLogic file/system log level

    Usage:
      log-level [options] [--] [<level>]

    Arguments:
      level                          The log level to set. Omit to show the current level.

    Options:
      -e, --environment=ENVIRONMENT  The ML Client environment name [default: "local"]
      -c, --connection=CONNECTION    Connection identifier from the environment or TCP port
      -t, --type=TYPE                The log type: file or system [default: "file"]
      -g, --group=GROUP              The group to target [default: "Default"]
      -s, --server=SERVER            The App Server to target (file log level only)
      -h, --help                     Display help for the given command. When no command is given display help for the list command.
      -q, --quiet                    Do not output any message.
      -V, --version                  Display this application version.
          --ansi                     Force ANSI output.
          --no-ansi                  Disable ANSI output.
      -n, --no-interaction           Do not ask any interactive question.
      -v|vv|vvv, --verbose           Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.


With a ``level`` argument the command sets the level; without one it shows the
current level. The output block is identical either way.

The command evaluates the MarkLogic Admin module functions on the connected
REST App-Server (see :doc:`../setup`). When the connecting user lacks the
privileges, it falls back to the Management REST API: reading App Server
properties requires ``manage-user``; reading group properties or changing
either target requires ``manage-admin`` (or equivalent privileges). When both
paths are refused, the command reports which Management role grants access.
Non-privilege failures retain the server error instead of reporting missing roles. Transport failures propagate
without retrying through Management REST.

.. caution::

    The REST App-Server the command connects to (``-c``, ``--connection``) is
    distinct from the App Server whose log level is shown or set
    (``--server``). App Servers have no system log level, so ``--server`` may
    only be combined with ``--type file``.


Show a log level
----------------

The group file log level is shown by default:

.. code-block:: bash

    ml log-level

.. code-block:: none

    Group: Default
    File Log Level: info

Target a group's system log level, or a specific App Server's file log level:

.. code-block:: bash

    ml log-level --type system --group Analyzer
    ml log-level --server App-Services


Set a log level
---------------

Pass the new level as the argument:

.. code-block:: bash

    ml log-level debug
    ml log-level --server App-Services warning

The supported levels are: ``finest``, ``finer``, ``fine``, ``debug``,
``config``, ``info``, ``notice``, ``warning``, ``error``, ``critical``,
``alert``, ``emergency``.

``-c / --connection`` accepts an environment connection identifier or a TCP
port (1-65535). A port overrides the default REST connection port, retaining
its other settings. Omit it to use the default REST connection.

Log-level diagnostics are available with ``ml log-level -vv``. Debug messages
show the eval attempt (which runs the Admin module), authorization failures
that trigger Manage REST fallback, and the result or reason for failure.
There is no separate Admin REST fallback.
