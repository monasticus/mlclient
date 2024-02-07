call eval
=========

.. code-block:: none

    Description:
      Sends a GET request to the /v1/eval endpoint

    Usage:
      call eval [options] [--] <code>

    Arguments:
      code                           The code to evaluate (a file path or raw xqy/js code)

    Options:
      -e, --environment=ENVIRONMENT  The ML Client environment name [default: "local"]
      -s, --rest-server=REST-SERVER  The ML REST Server environmental id
          --var=VAR                  A variable to be used in the code (multiple values allowed)
      -x, --xquery                   If set, the code will be treated as raw xquery
      -j, --javascript               If set, the code will be treated as raw javascript
      -d, --database=DATABASE        Evaluate the code on the named content database
      -t, --txid=TXID                The transaction identifier of the multi-statement transaction

      -h, --help                     Display help for the given command. When no command is given display help for the list command.
      -q, --quiet                    Do not output any message.
      -V, --version                  Display this application version.
          --ansi                     Force ANSI output.
          --no-ansi                  Disable ANSI output.
      -n, --no-interaction           Do not ask any interactive question.
      -v|vv|vvv, --verbose           Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.


Evaluate code from a file
-------------------------

.. code-block:: bash

    ml call eval -s app-services ./xqy-code-to-eval.xqy

.. code-block:: bash

    ml call eval -s app-services ./js-code-to-eval.js


Evaluate raw xquery code
------------------------

.. code-block:: bash

    ml call eval -s app-services -x 'fn:current-dateTime()'


Evaluate raw javascript code
----------------------------

.. code-block:: bash

    ml call eval -s app-services -j 'fn.currentDateTime()'


Evaluate code with variables
----------------------------

.. code-block:: bash

    ml call eval -s app-services -var DAYS=5 ./xqy-code-to-eval.xqy

.. code-block:: bash

    ml call eval -s app-services -x --var DAYS=5 '
    > declare variable $DAYS external;
    >
    > fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'


.. code-block:: bash

    ml call eval -s app-services -j --var days=5 '
    > fn.currentDateTime().subtract(xs.dayTimeDuration(`P${days}D`))'


Evaluate code with variables within a namespace
-----------------------------------------------

.. code-block:: bash

    ml call eval \
    > -s app-services \
    > -x \
    > --var {http://www.w3.org/2005/xquery-local-functions}DAYS=5 '
    > declare variable $local:DAYS external;
    >
    > fn:current-dateTime() - xs:dayTimeDuration("P" || $local:DAYS || "D")'


Evaluate code on a custom database
----------------------------------

.. code-block:: bash

    ml call eval -s app-services -d Security ./xqy-code-to-eval.xqy
