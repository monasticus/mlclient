call logs
=========

.. code-block:: none

    Description:
      Sends a GET request to the /manage/v2/logs endpoint

    Usage:
      call logs [options]

    Options:
      -e, --environment=ENVIRONMENT  The ML Client environment name [default: "local"]
      -a, --app-server=APP-SERVER    The App-Server (port) to get logs of
      -s, --rest-server=REST-SERVER  The ML REST Server environmental id (to get logs from)
      -l, --log-type=LOG-TYPE        MarkLogic log type (error, access or request) [default: "error"]
      -f, --from=FROM                A start time to search error logs
      -t, --to=TO                    n end time to search error logs
      -r, --regex=REGEX              A regex to search error logs
      -H, --host=HOST                The host from which to return the log data.
          --list                     If set, no filename will be passed to the Logs REST API

      -h, --help                     Display help for the given command. When no command is given display help for the list command.
      -q, --quiet                    Do not output any message.
      -V, --version                  Display this application version.
          --ansi                     Force ANSI output.
          --no-ansi                  Disable ANSI output.
      -n, --no-interaction           Do not ask any interactive question.
      -v|vv|vvv, --verbose           Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.


List log file names
-------------------

.. code-block:: bash

    ml call logs --list


Get all logs
------------

.. code-block:: bash

    ml call logs -a 8002

.. code-block:: bash

    ml call logs -a 8002 -l error

.. code-block:: bash

    ml call logs -a 8002 -l access

.. code-block:: bash

    ml call logs -a 8002 -l request


Get limited logs
----------------
.. note::

    ``--from``, ``--to`` and ``--regex`` parameters work only for error logs


Time frames
^^^^^^^^^^^

.. code-block:: bash

    ml call logs -a 8002 -f 10:00

.. code-block:: bash

    ml call logs -a 8002 -t 12:00

.. code-block:: bash

    ml call logs -a 8002 -f 10:00 -t 12:00

.. code-block:: bash

    ml call logs -a 8002 -f 2024-02-01 -t 2024-02-03

.. code-block:: bash

    ml call logs -a 8002 -f '2024-02-01 10:00' -t 2024-02-03


RegEx
^^^^^

.. code-block:: bash

    ml call logs -a 8002 -r 'Forest Meters'

.. code-block:: bash

    ml call logs -a 8002 -r 'Forest M.*'

.. code-block:: bash

    ml call logs -a 8002 -r 'Memory [^1]{1,2}%'
