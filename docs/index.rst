.. MLClient documentation master file, created by
   sphinx-quickstart on Mon Aug  7 10:42:08 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

MLClient - MarkLogic instance in your hands
===========================================

.. image:: https://img.shields.io/badge/GitHub-monasticus%2Fmlclient-white?style=plastic&logo=github&color=white
    :target: https://github.com/monasticus/mlclient
    :alt: Tag Badge

.. image:: https://img.shields.io/github/license/monasticus/mlclient?label=License&style=plastic
    :target: https://github.com/monasticus/mlclient/blob/main/LICENSE
    :alt: License Badge

.. image:: https://img.shields.io/pypi/pyversions/mlclient?label=Python&style=plastic
    :target: https://www.python.org/
    :alt: Python Version Support Badge

ML Client is a python library providing a python API to manage a MarkLogic instance.
Furthermore, it includes a Command Line Interface.

Below you can find a few examples of basic usage. Read more in the deep documentation.

-------------------

Low-level (raw HTTP)::

   >>> from mlclient import MLClient
   >>> config = {
   ...     "host": "localhost",
   ...     "port": 8002,
   ...     "username": "admin",
   ...     "password": "admin",
   ... }
   >>> with MLClient(**config) as ml:
   ...     resp = ml.http.post(
   ...         "/v1/eval",
   ...         body={"xquery": "xdmp:database() => xdmp:database-name()"},
   ...     )
   ...     print(resp.text)
   ...
   --6a5df7d535c71968
   Content-Type: text/plain
   X-Primitive: string

   App-Services
   --6a5df7d535c71968--


Mid-level REST API (/v1/*)::

   >>> from mlclient import MLClient
   >>> config = {
   ...     "host": "localhost",
   ...     "port": 8002,
   ...     "username": "admin",
   ...     "password": "admin",
   ... }
   >>> with MLClient(**config) as ml:
   ...     resp = ml.rest.eval.post(
   ...         xquery="xdmp:database() => xdmp:database-name()",
   ...     )
   ...     print(resp.text)
   ...
   --6a5df7d535c71968
   Content-Type: text/plain
   X-Primitive: string

   App-Services
   --6a5df7d535c71968--


Response parsing::

   >>> from mlclient import MLClient, MLResponseParser
   >>> config = {
   ...     "host": "localhost",
   ...     "port": 8002,
   ...     "username": "admin",
   ...     "password": "admin",
   ... }
   >>> with MLClient(**config) as ml:
   ...     resp = ml.rest.eval.post(
   ...         xquery="xdmp:database() => xdmp:database-name()",
   ...     )
   ...     parsed = MLResponseParser.parse(resp)
   ...     print(parsed)
   ...
   App-Services


Mid-level Management API (/manage/v2/*)::

   >>> from mlclient import MLClient
   >>> config = {
   ...     "host": "localhost",
   ...     "port": 8002,
   ...     "username": "admin",
   ...     "password": "admin",
   ... }
   >>> with MLClient(**config) as ml:
   ...     resp = ml.manage.databases.get_list()


High-level (services)::

   >>> from mlclient import MLClient
   >>> config = {
   ...     "host": "localhost",
   ...     "port": 8002,
   ...     "username": "admin",
   ...     "password": "admin",
   ... }
   >>> with MLClient(**config) as ml:
   ...     result = ml.eval.xquery(
   ...         "xdmp:database() => xdmp:database-name()",
   ...     )
   ...     print(result)
   ...
   App-Services

.. toctree::
   :maxdepth: 1
   :caption: Python API:

   api/mlclient/mlclient

.. toctree::
   :maxdepth: 1
   :caption: User Guide:

   user/setup
   user/cli
   user/pythonapi



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
