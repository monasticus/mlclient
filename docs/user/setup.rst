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
the root value. This mirrors the :class:`~mlclient.MLClient` connection model -
see :doc:`pythonapi/core` for the full matrix of connection modes and auth
methods. For example, an HTTPS environment with a mutual-TLS app server:

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

The ``auth`` field accepts the same string shortcuts as the Python API:
``digest``, ``basic``, ``digestbasic``, ``certificate``, and ``kerberos``. A
server presenting a client certificate may leave ``auth`` unset (it defaults to
``certificate``), set ``auth: certificate`` explicitly, or set a credential
method such as ``auth: digest`` for double auth - the certificate then sets up
mutual TLS while the credential carries the user identity.

A MarkLogic Cloud environment declares ``cloud`` at the root and omits
``protocol`` and ``auth`` (Cloud forces HTTPS and authenticates via its API key):

   .. code-block:: yaml

      app-name: migration-app
      host: my-org.marklogic.cloud
      cloud:
        api-key: my-api-key
        base-path: /ml/my-instance
      app-servers:
        - id: content
          port: 8100

MLEnvironment class
-------------------
Having the environment file, you can instantiate ``MLEnvironment`` class using your environment::

   >>> from mlclient import MLEnvironment
   >>> env = MLEnvironment.load("local")
   >>> env
   MLEnvironment(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', auth='digest', ssl=None, cloud=None, app_servers=[MLServerConfig(identifier='manage', port=8002, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='content', port=8100, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='modules', port=8101, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='schemas', port=8102, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='test', port=8103, auth='basic', username=None, password=None, ssl=None, rest=False)])

This code will work in every subdirectory of the ``migration-app`` project as it looks for ``.mlclient`` recursively.

``MLEnvironment`` class allows you to get a specific app service config::

   >>> from mlclient import MLClient, MLEnvironment
   >>> env = MLEnvironment.load("local")
   >>> with MLClient(**env.provide_config("content")) as ml:
   ...     result = ml.eval.xquery("xdmp:database() => xdmp:database-name()")
   ...


.. note::
   If you want to load an environment from a specific file path instead of relying on
   the ``.mlclient`` directory lookup, you can use ``MLEnvironment.load_file()``::

       >>> from mlclient import MLEnvironment
       >>> env = MLEnvironment.load_file("path/to/mlclient-local.yaml")
       >>> env
       MLEnvironment(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', auth='digest', ssl=None, cloud=None, app_servers=[MLServerConfig(identifier='manage', port=8002, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='content', port=8100, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='modules', port=8101, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='schemas', port=8102, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='test', port=8103, auth='basic', username=None, password=None, ssl=None, rest=False)])


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
