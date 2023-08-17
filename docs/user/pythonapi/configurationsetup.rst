MLClient Configuration Setup
============================

The ``mlclient`` library provides a simple API to manage your ML instance configuration.
Using a YAML file, you're able to easily get a configuration for a MLClient instance.

YAML Configuration file
-----------------------

Assume you want to manage your ML application called *migration-app*.
To integrate your project with **MLClient**, create a YAML file:

   .. literalinclude:: mlclient-local.yaml
      :language: YAML


MLConfiguration.from_file()
---------------------------
Having the configuration file, you can instantiate ``MLConfiguration`` class using ``MLConfiguration.from_file()`` method::

   >>> from mlclient import MLConfiguration
   >>> ml_config = MLConfiguration.from_file("mlclient-local.yaml")
   >>> ml_config
   MLConfiguration(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', app_servers=[MLAppServerConfiguration(identifier='manage', port=8002, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='content', port=8100, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='modules', port=8101, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='schemas', port=8102, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='test', port=8103, auth=<AuthMethod.BASIC: 'basic'>)])


MLConfiguration.from_environment()
----------------------------------
However, we encourage you to go one step further and setup **MLClient** configuration.
To do that, simply create ``.mlclient`` directory in you project's root, and move your configuration file there.
To make your configuration recognizable for **MLClient** as an ML environment, it needs to follow just two rules:

* The configuration file needs to be placed in *<your project>*/.mlclient
* The configuration file needs to be named mlclient-*<environment>*.yaml

Then you can instantiate ``MLConfiguration`` using ``MLConfiguration.from_environment()`` method::

   >>> from mlclient import MLConfiguration
   >>> ml_config = MLConfiguration.from_environment("local")
   >>> ml_config
   MLConfiguration(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', app_servers=[MLAppServerConfiguration(identifier='manage', port=8002, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='content', port=8100, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='modules', port=8101, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='schemas', port=8102, auth=<AuthMethod.BASIC: 'basic'>), MLAppServerConfiguration(identifier='test', port=8103, auth=<AuthMethod.BASIC: 'basic'>)])


Providing an MLClient's config
------------------------------

Now you can use your MarkLogic configuration to get a specific app service config::

   >>> from mlclient import MLConfiguration
   >>> ml_config = MLConfiguration.from_environment("local")
   >>> app_config = ml_config.provide_config("content")
   >>> with MLResourceClient(**app_config) as client:
   ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
   ...     parsed_resp = MLResponseParser.parse(resp)
   ...



