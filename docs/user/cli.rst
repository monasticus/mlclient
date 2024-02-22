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
      help       Displays help for a command.
      list       Lists commands.

     call
      call eval  Sends a GET request to the /v1/eval endpoint
      call logs  Sends a GET request to the /manage/v2/logs endpoint

.. caution::

    All MLClient commands use MLClient Configuration. To set it up, see :doc:`./setup`.

.. toctree::
   :maxdepth: 1
   :hidden:

   cli/call

