Project Integration
===================

When using **ML Client** in your application it can be helpful to setup **ML Client**'s configuration.
It will make it easier to use ``mlclient`` lib without explicit use of ML configuration parameters.
Using a YAML file, you're able to easily get a configuration for a MLClient instance.

YAML Configuration file
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

   .. literalinclude:: mlclient-local.yaml
      :language: YAML

MLConfiguration class
---------------------
Having the configuration file, you can instantiate ``MLConfiguration`` class using your environment::

   >>> from mlclient import MLConfiguration
   >>> ml_config = MLConfiguration.from_environment("local")
   >>> ml_config
   MLConfiguration(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', app_servers=[MLAppServerConfiguration(identifier='manage', port=8002, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='content', port=8100, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='modules', port=8101, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='schemas', port=8102, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='test', port=8103, auth=<AuthMethod.BASIC: 'basic'>)])

This code will work in every subdirectory of the ``migration-app`` project as it looks for ``.mlclient`` recursively.

``MLConfiguration`` class allows you to get a specific app service config::

   >>> from mlclient import MLConfiguration
   >>> ml_config = MLConfiguration.from_environment("local")
   >>> app_config = ml_config.provide_config("content")
   >>> with MLResourceClient(**app_config) as client:
   ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
   ...     parsed_resp = MLResponseParser.parse(resp)
   ...


.. note::
   If you would like to use MLConfiguration class without project integration,
   you can use ``MLConfiguration.from_file()`` method::

       >>> from mlclient import MLConfiguration
       >>> ml_config = MLConfiguration.from_file("mlclient.yaml")
       >>> ml_config
       MLConfiguration(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', app_servers=[MLAppServerConfiguration(identifier='manage', port=8002, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='content', port=8100, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='modules', port=8101, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='schemas', port=8102, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='test', port=8103, auth=<AuthMethod.BASIC: 'basic'>)])


MLManager class
---------------

To make it easier, ``mlclient`` lib provides you a ``MLManager`` class with the highest-level API.
The same logic as in the above example we will achieve in fewer steps::
   >>> from mlclient import MLManager
   >>> ml_manager = MLManager("local")
   >>> with ml_manager.get_resources_client("content") as client:
   ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
   ...     parsed_resp = MLResponseParser.parse(resp)
   ...
The same logic as in the above example we will achieve in fewer steps::
   >>> from mlclient import MLManager
   >>> ml_manager = MLManager("local")
   >>> with ml_manager.get_resources_client("content") as client:
   ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
   ...     parsed_resp = MLResponseParser.parse(resp)
   ...
The same logic as in the above example we will achieve in fewer steps::
   >>> from mlclient import MLManager
   >>> ml_manager = MLManager("local")
   >>> with ml_manager.get_resource_client("content") as client:
   ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
   ...     parsed_resp = MLResponseParser.parse(resp)
   ...

.. note::
   ``MLManager`` is accessible only using ML Client Environments.
