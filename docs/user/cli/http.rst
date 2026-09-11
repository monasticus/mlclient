http
====

.. code-block:: none

    Description:
      Sends a raw HTTP request to any REST endpoint

    Usage:
      http [options] [--] <method> <endpoint> [<params>...]

    Arguments:
      method                         The HTTP method (e.g. get, head, post, put, delete, patch)
      endpoint                       The REST endpoint to call (e.g. /v1/documents)
      params                         Query params (key=value) and headers (key:value)

    Options:
      -e, --environment=ENVIRONMENT  The ML Client environment name [default: "local"]
      -c, --connection=CONNECTION  Connection identifier from the environment or TCP port
      -b, --body=BODY                Request body: a raw string, a file path, or @file-path
      -i, --include                  Include the status line and response headers in the output
      -p, --pretty                   Pretty-print an XML or JSON body with a 2-space indent

      -h, --help                     Display help for the given command. When no command is given display help for the list command.
      -q, --quiet                    Do not output any message.
      -V, --version                  Display this application version.
          --ansi                     Force ANSI output.
          --no-ansi                  Disable ANSI output.
      -n, --no-interaction           Do not ask any interactive question.
      -v|vv|vvv, --verbose           Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.


A ``key=value`` token is sent as a query parameter, a ``key:value`` token as a request header.
``--body`` accepts a raw string, a file path, or ``@file-path`` (both path forms read the file).
By default only the response body is printed. ``--include`` prepends the status line and
response headers (the same protocol-like representation the client logs); a head request has
no body, so it always prints that representation.


get an endpoint
---------------

.. code-block:: bash

    ml http get /v1/documents uri=/doc.xml


Include status and headers
--------------------------

.. code-block:: bash

    ml http -i get /v1/documents uri=/doc.xml


head an endpoint
----------------

.. code-block:: bash

    ml http head /v1/documents uri=/doc.xml


post or put a body
------------------

.. code-block:: bash

    ml http post /v1/documents uri=/doc.xml Content-Type:application/xml -b '<doc/>'

.. code-block:: bash

    ml http put /v1/documents uri=/doc.xml Content-Type:application/xml -b @./doc.xml


delete a document
-----------------

.. code-block:: bash

    ml http delete /v1/documents uri=/doc.xml


Request and response handling
-----------------------------

``-c`` selects an App Server identifier from the environment, including
``manage`` or ``admin``. Without it, the default REST App Server is used;
endpoint paths do not automatically select a port. Paths may include a query
string; additional ``key=value`` tokens are appended. Repeat a query key to
send all values. Header names are case-insensitive; the last value wins.

.. code-block:: bash

    ml http -c manage get /manage/v2/hosts view=status format=json
    ml http get /v1/documents uri=/one.xml uri=/two.xml
    ml http -p get /v1/documents uri=/doc.json Accept:application/json

Body text is sent literally, including JSON. Files are read as bytes, preserving
binary data and line endings. An explicit ``@path`` must exist and be readable;
a long literal body is not rejected for exceeding filesystem path limits.

``--pretty`` formats valid JSON and element-only XML. Invalid JSON/XML, mixed
XML content and ``xml:space="preserve"`` remain unchanged. Output is decoded
response text. The status line reflects the actual HTTP protocol version.
Responses are printed before reporting a 4xx/5xx error with a nonzero exit code.
Redirect responses are displayed without following them and do not count as
HTTP errors.

``-c / --connection`` accepts an environment connection identifier or a TCP
port (1-65535). A port overrides the default REST connection port, retaining
its other settings. Omit it to use the default REST connection.
