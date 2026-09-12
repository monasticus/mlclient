env init
========

.. code-block:: none

    Description:
      Scaffolds an MLClient environment configuration file

    Usage:
      env init [options] [--] [<name>]

    Arguments:
      name                             The environment name. Omit to run the interactive wizard.

    Options:
      -i, --interactive                Run the wizard even when a name is given
          --from-gradle[=FROM-GRADLE]  Derive from ml-gradle properties (an env name or a file path)
          --from-host[=FROM-HOST]      Derive by querying a MarkLogic host ([protocol://]host[:port])
          --app-name=APP-NAME          Application label; scopes --from-host to matching servers
      -u, --username=USERNAME          Username for --from-host
      -p, --password=PASSWORD          Password for --from-host
      -a, --auth=AUTH                  Auth method for --from-host (basic, digest or digestbasic)
      -g, --global                     Write to the home directory instead of the current directory
      -f, --force                      Overwrite an existing configuration file
      -h, --help                       Display help for the given command. When no command is given display help for the list command.
      -q, --quiet                      Do not output any message.
      -V, --version                    Display this application version.
          --ansi                       Force ANSI output.
          --no-ansi                    Disable ANSI output.
      -n, --no-interaction             Do not ask any interactive question.
      -v|vv|vvv, --verbose             Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.


The command writes ``.mlclient/mlclient-<name>.yaml`` in the current directory,
or in your home directory with ``--global``. It refuses to overwrite an existing
file unless you pass ``--force``. To load the result, see :doc:`../../setup`.

There are three sources for a new environment: a blank commented template, a set
of ml-gradle properties (``--from-gradle``), or a running MarkLogic instance
queried over its Manage API (``--from-host``).


Scaffold a blank template
--------------------------

Passing only a name writes a fully commented template you can edit by hand:

.. code-block:: bash

    ml env init local

With no name - or with ``--interactive`` even when a name is given - the command
runs a short wizard that asks for the name, then a source
(``blank`` / ``gradle`` / ``server``):

.. code-block:: bash

    ml env init

.. code-block:: bash

    ml env init local --interactive


Derive from ml-gradle properties
--------------------------------

``--from-gradle`` reads an ml-gradle setup. A selector ending in ``.properties``
is a file path; anything else is an environment name. A name reads
``gradle-<env>.properties`` from the current directory merged over
``gradle.properties`` and doubles as the environment name:

.. code-block:: bash

    ml env init --from-gradle=dev

Give an explicit name to override the derived one:

.. code-block:: bash

    ml env init my-dev --from-gradle=dev

A file-path selector is parsed on its own, with no overlay merge, and has no name
to borrow, so the command prompts for one:

.. code-block:: bash

    ml env init --from-gradle=./gradle-dev.properties

The gradle source is validated before anything is prompted: an unknown
environment name is reported with the available profiles, and a missing file is
reported with the ``.properties`` files found in its directory.

Passing ``--from-gradle`` with no value prompts for both the name and the
selector, and ``--interactive`` forces the name prompt even for a derivable name:

.. code-block:: bash

    ml env init --from-gradle

.. code-block:: bash

    ml env init --from-gradle=dev --interactive


Derive from a running host
--------------------------

``--from-host`` connects to a MarkLogic host's Manage server and maps its App
Servers into an environment. When both the environment name and ``--from-host``
are present, the command is non-interactive unless ``--interactive`` is also
passed. Missing connection fields then use ``http``, ``localhost``, port ``8002``,
user ``admin``, password ``admin``, and ``digest`` authentication:

.. code-block:: bash

    ml env init local --from-host

The value accepts ``host``, ``host:port`` or a URL with a protocol
(``protocol://host[:port]``). The port defaults to the Manage port 8002 and the
protocol defaults to ``http``; ``https`` connects over TLS. Because dev MarkLogic
serves self-signed certificates, ``https`` discovery skips certificate
verification and writes ``ssl: {verify: false}`` into the generated file so it
loads the same way; point ``ssl.verify`` at a CA bundle for a trusted cert. An
explicit protocol and port are used for the connection:

.. code-block:: bash

    ml env init prod --from-host=https://ml.example.com:9000 --username=admin --password=secret

When the name is omitted, or ``--interactive`` is passed, the command asks only
for values not supplied through options. The password is not echoed:

.. code-block:: bash

    ml env init --from-host

.. code-block:: bash

    ml env init prod --from-host=ml.example.com:8002 --username=admin --interactive

The ``server`` source in the wizard also honours ``--username``, ``--password``
and ``--auth``. An explicit empty password (``--password=''``) is preserved;
pressing Enter at the password prompt accepts the displayed ``admin`` default.

``--auth`` selects the client authentication method and accepts ``basic``,
``digest`` (the default) or ``digestbasic``; any other value is rejected:

.. code-block:: bash

    ml env init prod --from-host=ml.example.com -u admin -p secret --auth=basic

Before querying the Manage API the command prints the target URL. Generated
YAML omits unchanged predefined servers and includes a comment listing their
defaults: ``app-services`` (8000), ``manage`` (8002), ``admin`` (8001), and
``health`` (7997, application-level auth).

Overrides retain the port and authentication needed to reproduce the discovered
connection when the generated file is loaded. A server whose authentication scheme
has no MLClient equivalent (``saml``) is skipped with a logged warning, since it
cannot be reproduced. An ``oauth`` scheme is kept as-is - add the bearer token
before loading the environment.

When the host is a name rather than ``localhost`` or a bare IP address, the
connection is assumed to pass through a load balancer that terminates it, so each
server inherits the root protocol and authentication and their own listener
settings are not recorded. A ``localhost`` or IP host reaches MarkLogic directly,
so each server's own protocol and authentication are written out where they
diverge from the root.

``--app-name`` both labels the environment and scopes discovery to the servers
whose name matches it; without it every discovered server is kept and the label
is left commented out:

.. code-block:: bash

    ml env init prod --from-host=ml.example.com -u admin -p secret --app-name=my-app
