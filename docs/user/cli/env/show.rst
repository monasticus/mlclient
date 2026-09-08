env show
========

.. code-block:: none

    Description:
      Lists MLClient environments, or renders one environment's settings

    Usage:
      env show [options] [--] [<name>] [<setting>]

    Arguments:
      name                 The environment name. Omit to list the available environments.
      setting              A root setting name (host, protocol, ...) or an app server id.

    Options:
      -g, --global         Read from the home directory instead of the current directory
          --raw            Print the raw configuration file instead of a rendered table
      -s, --secrets        Reveal secret values instead of masking them

      -h, --help           Display help for the given command. When no command is given display help for the list command.
      -q, --quiet          Do not output any message.
      -V, --version        Display this application version.
          --ansi           Force ANSI output.
          --no-ansi        Disable ANSI output.
      -n, --no-interaction Do not ask any interactive question.
      -v|vv|vvv, --verbose Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.

The command reads the nearest ``.mlclient`` directory - the current directory
or the closest ancestor that has one - or your home directory's with
``--global``:

.. code-block:: bash

    ml env show --global


List the environments
----------------------

With no name it prints the environment names found in ``.mlclient``, one per
line - the ``<name>`` part of each ``mlclient-<name>.yaml`` file:

.. code-block:: bash

    ml env show


Render one environment
----------------------

Given a name it renders that environment's settings as a table, with the app
servers in a second table. Passwords and other secrets are masked:

.. code-block:: bash

    ml env show local

Pass ``--raw`` to print the configuration file verbatim instead - no table, no
masking:

.. code-block:: bash

    ml env show local --raw

Pass ``--secrets`` (``-s``) to keep the rendered table but reveal the secret
values instead of masking them:

.. code-block:: bash

    ml env show local --secrets


Narrow to a single setting or server
------------------------------------

A second argument narrows the view. A root setting name prints just its value
(masked when it is a secret):

.. code-block:: bash

    ml env show local host

An app server id renders that server's own settings as a key/value table. This
also covers the predefined servers (``app-services``, ``manage``, ``admin``,
``health``) even when the file does not list them - their defaults are shown:

.. code-block:: bash

    ml env show local rest
