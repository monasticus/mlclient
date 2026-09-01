Setup
=====

When using **ML Client** in your application it can be helpful to setup **ML Client**'s environment.
It will make it easier to use ``mlclient`` lib without explicit use of ML configuration parameters.
Using a YAML file, you're able to easily get a configuration for a MLClient instance.

YAML Environment file
-----------------------

Assume you want to manage your ML application called *migration-app*.
First create a ``.mlclient`` directory in root of your project and a YAML file within::

   migration-app
   ├── .mlclient
   │   └── mlclient-local.yaml
   ├── src
   ├── tests
   └── pyproject.toml

YAML file:

   .. literalinclude:: setup/mlclient-local.yaml
      :language: YAML

Root-level defaults and per-server overrides
---------------------------------------------

Connection and authentication settings declared at the top level of the file
(``protocol``, ``host``, ``username``, ``password``, ``auth``, ``ssl``, ``cloud``)
act as defaults for every app server. Any of ``auth``, ``username``,
``password``, or ``ssl`` may be overridden per server; an unset field inherits
the root value. ``auth``, ``username`` and ``password`` replace the root value
wholesale, while ``ssl`` merges field by field: a server declaring only a client
certificate keeps the root's server verification (see below). This mirrors the
:class:`~mlclient.MLClient` connection model - see :doc:`pythonapi/core` for the
full matrix of connection modes and auth methods. For example, an HTTPS
environment with a mutual-TLS app server:

   .. code-block:: yaml

      app-name: migration-app
      protocol: https
      host: ml.example.com
      username: admin
      password: admin
      auth: digest
      ssl:
        verify: /etc/ssl/corp-ca.pem
      app-servers:

        - id: content
          port: 8100

        - id: secure
          port: 8200
          ssl:
            cert_file: /client.pem
            key_file: /client-key.pem

The ``content`` server inherits the root digest auth and CA bundle, while
``secure`` presents a client certificate and so authenticates via mutual TLS.
Because ``ssl`` merges, ``secure`` keeps the root's ``verify: /etc/ssl/corp-ca.pem``
even though it only declares ``cert_file`` and ``key_file``. A server overrides a
single SSL field by setting it explicitly - ``verify: /etc/ssl/other-ca.pem`` for
a different CA bundle, or ``verify: false`` to disable server verification for
that server alone - while every unset field still inherits from the root.

The ``auth`` field accepts the same string shortcuts as the Python API:
``digest``, ``basic``, ``digestbasic``, ``certificate``, and ``kerberos``. A
server presenting a client certificate may leave ``auth`` unset (it defaults to
``certificate``), set ``auth: certificate`` explicitly, or set a credential
method such as ``auth: digest`` for double auth - the certificate then sets up
mutual TLS while the credential carries the user identity.

A MarkLogic Cloud environment declares ``cloud`` at the root and omits
``protocol`` and ``auth`` (Cloud forces HTTPS and authenticates via its API key).
Cloud collapses every tier onto a single HTTPS connection on port 443, routing
each one through the ``base-path`` rather than a distinct port. Because there is
only one connection and its port is fixed, a Cloud environment needs no
``app-servers`` section at all - the default REST app server is enough:

   .. code-block:: yaml

      app-name: migration-app
      host: my-org.marklogic.cloud
      cloud:
        api-key: my-api-key
        base-path: /ml/my-instance

``port`` is optional everywhere and defaults to the connection's own port (8000
for on-premises, 443 for Cloud), so it need only be set for app servers on a
non-default port. Declare ``app-servers`` explicitly only to name additional
servers or override per-server settings.

Three app servers are always present even when you list none: ``app-services``
(the port-8000 REST server), ``manage`` (8002), and ``admin`` (8001). Anything
you declare is added to them; an entry whose ``id`` matches one of the three
overrides that predefined server - for example, declaring ``admin`` on a
non-standard port or ``app-services`` with ``rest: false``.

MLEnvironment class
-------------------
Having the environment file, you can instantiate ``MLEnvironment`` class using your environment::

   >>> from mlclient import MLEnvironment
   >>> env = MLEnvironment.load("local")
   >>> env
   MLEnvironment(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', auth='digest', ssl=None, cloud=None, app_servers=[MLServerConfig(identifier='manage', port=8002, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='content', port=8100, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='modules', port=8101, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='schemas', port=8102, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='test', port=8103, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='app-services', port=None, protocol=None, auth=None, username=None, password=None, ssl=None, rest=True), MLServerConfig(identifier='admin', port=8001, protocol=None, auth=None, username=None, password=None, ssl=None, rest=False)])

This code will work in every subdirectory of the ``migration-app`` project as it looks for ``.mlclient`` recursively.

``MLEnvironment`` class allows you to get a specific app service config::

   >>> from mlclient import MLClient, MLEnvironment
   >>> env = MLEnvironment.load("local")
   >>> with MLClient(config=env.provide_config("content")) as ml:
   ...     result = ml.eval.xquery("xdmp:database() => xdmp:database-name()")
   ...


.. note::
   If you want to load an environment from a specific file path instead of relying on
   the ``.mlclient`` directory lookup, you can use ``MLEnvironment.load_file()``::

       >>> from mlclient import MLEnvironment
       >>> env = MLEnvironment.load_file("path/to/mlclient-local.yaml")
       >>> env
       MLEnvironment(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', auth='digest', ssl=None, cloud=None, app_servers=[MLServerConfig(identifier='manage', port=8002, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='content', port=8100, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='modules', port=8101, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='schemas', port=8102, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='test', port=8103, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='app-services', port=None, protocol=None, auth=None, username=None, password=None, ssl=None, rest=True), MLServerConfig(identifier='admin', port=8001, protocol=None, auth=None, username=None, password=None, ssl=None, rest=False)])


MLClientManager class
---------------------

To make it easier, ``mlclient`` lib provides you a ``MLClientManager`` class with the highest-level API.
The same logic as in the above example we will achieve in fewer steps::

   >>> from mlclient import MLClientManager
   >>> mgr = MLClientManager("local")
   >>> with mgr.get_client("content") as ml:
   ...     result = ml.eval.xquery("xdmp:database() => xdmp:database-name()")
   ...

.. note::
   ``MLClientManager`` is accessible only using ML Client Environments.
