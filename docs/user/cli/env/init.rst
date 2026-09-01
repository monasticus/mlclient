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
          --from-host[=FROM-HOST]      Derive by querying a MarkLogic host (host[:port])
          --app-name=APP-NAME          Application label; scopes --from-host to matching servers
      -u, --username=USERNAME          Username for --from-host
      -p, --password=PASSWORD          Password for --from-host (prompted if omitted)
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
queried over its Manage API (``--from-host``). Each source resolves whatever it
needs, prompting only for what the command line left out.


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

``--from-gradle`` reads an ml-gradle setup. Its value is either an environment
name (``gradle.properties`` merged with ``gradle-<env>.properties``) or a path to
a properties file. A plain environment-name selector doubles as the environment
name:

.. code-block:: bash

    ml env init --from-gradle=dev

Give an explicit name to override the derived one:

.. code-block:: bash

    ml env init my-dev --from-gradle=dev

A properties-file selector has no name to borrow, so the command prompts for one:

.. code-block:: bash

    ml env init --from-gradle=./gradle-dev.properties

Passing ``--from-gradle`` with no value prompts for both the name and the
selector, and ``--interactive`` forces the name prompt even for a derivable name:

.. code-block:: bash

    ml env init --from-gradle

.. code-block:: bash

    ml env init --from-gradle=dev --interactive


Derive from a running host
--------------------------

``--from-host`` connects to a MarkLogic host's Manage server and maps its App
Servers into an environment. Give the connection fully to resolve without any
prompt:

.. code-block:: bash

    ml env init prod --from-host=ml.example.com --username=admin --password=secret

The value accepts ``host`` or ``host:port`` (the port defaults to the Manage port
8002). Any of the name, username, password and auth method that you omit is
prompted for; the password is never echoed:

.. code-block:: bash

    ml env init prod --from-host=ml.example.com:8002 --username=admin

Passing ``--from-host`` with no value prompts for every connection field:

.. code-block:: bash

    ml env init --from-host

``--auth`` selects the client authentication method and accepts ``basic``,
``digest`` (the default) or ``digestbasic``; any other value is rejected:

.. code-block:: bash

    ml env init prod --from-host=ml.example.com -u admin -p secret --auth=basic

``--app-name`` both labels the environment and scopes discovery to the servers
whose name matches it; without it every discovered server is kept and the label
is left commented out:

.. code-block:: bash

    ml env init prod --from-host=ml.example.com -u admin -p secret --app-name=my-app
