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

MLEnvironment class
-------------------
Having the environment file, you can instantiate ``MLEnvironment`` class using your environment::

   >>> from mlclient import MLEnvironment
   >>> env = MLEnvironment.load("local")
   >>> env
   MLEnvironment(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', app_servers=[MLServerConfig(identifier='manage', port=8002, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='content', port=8100, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='modules', port=8101, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='schemas', port=8102, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='test', port=8103, auth=<AuthMethod.BASIC: 'basic'>)])

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
       MLEnvironment(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', app_servers=[MLServerConfig(identifier='manage', port=8002, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='content', port=8100, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='modules', port=8101, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='schemas', port=8102, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='test', port=8103, auth=<AuthMethod.BASIC: 'basic'>)])


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
