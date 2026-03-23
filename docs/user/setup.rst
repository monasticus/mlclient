Setup
=====

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

   .. literalinclude:: setup/mlclient-local.yaml
      :language: YAML

MLProfile class
---------------
Having the configuration file, you can instantiate ``MLProfile`` class using your profile::

   >>> from mlclient import MLProfile
   >>> profile = MLProfile.load("local")
   >>> profile
   MLProfile(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', app_servers=[MLServerConfig(identifier='manage', port=8002, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='content', port=8100, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='modules', port=8101, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='schemas', port=8102, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='test', port=8103, auth=<AuthMethod.BASIC: 'basic'>)])

This code will work in every subdirectory of the ``migration-app`` project as it looks for ``.mlclient`` recursively.

``MLProfile`` class allows you to get a specific app service config::

   >>> from mlclient import MLClient, MLProfile
   >>> profile = MLProfile.load("local")
   >>> app_config = profile.provide_config("content")
   >>> with MLClient(**app_config) as ml:
   ...     result = ml.eval.xquery("xdmp:database() => xdmp:database-name()")
   ...


.. note::
   If you would like to use MLProfile class without setting up a profile,
   you can use ``MLProfile.load_file()`` method::

       >>> from mlclient import MLProfile
       >>> profile = MLProfile.load_file("mlclient.yaml")
       >>> profile
       MLProfile(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', app_servers=[MLServerConfig(identifier='manage', port=8002, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='content', port=8100, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='modules', port=8101, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='schemas', port=8102, auth=<AuthMethod.BASIC: 'basic'>), MLServerConfig(identifier='test', port=8103, auth=<AuthMethod.BASIC: 'basic'>)])


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
   ``MLClientManager`` is accessible only using ML Client Profiles.
