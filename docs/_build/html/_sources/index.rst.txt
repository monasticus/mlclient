.. MLClient documentation master file, created by
   sphinx-quickstart on Mon Aug  7 10:42:08 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

MLClient - MarkLogic instance in your hands
===========================================

ML Client is a python library providing a python API to manage a MarkLogic instance.

Low-level MLClient::

   >>> from mlclient import MLClient
   >>> config = {
   ...     "host": "localhost",
   ...     "port": 8002,
   ...     "username": "admin",
   ...     "password": "admin",
   ... }
   >>> with MLClient(**config) as client:
   ...     resp = client.post(endpoint="/v1/eval",
   ...                        body={"xquery": "xdmp:database() => xdmp:database-name()"})
   ...     print(resp.text)
   ...
   --6a5df7d535c71968
   Content-Type: text/plain
   X-Primitive: string

   App-Services
   --6a5df7d535c71968--


Medium-level MLResourceClient::

   >>> from mlclient import MLResourceClient
   >>> config = {
   ...     "host": "localhost",
   ...     "port": 8002,
   ...     "username": "admin",
   ...     "password": "admin",
   ... }
   >>> with MLResourceClient(**config) as client:
   ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
   ...     print(resp.text)
   ...
   --6a5df7d535c71968
   Content-Type: text/plain
   X-Primitive: string

   App-Services
   --6a5df7d535c71968--

.. toctree::
   :maxdepth: 1
   :caption: Python API:

   mlclient/mlclient



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
