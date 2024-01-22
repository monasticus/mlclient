Basic Usage
===========

Send a custom request
---------------------

To send a custom request, simply import and use MLClient class::

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


Use MarkLogic REST Resources
----------------------------

MarkLogic have defined multiple REST Resources. The mlclient library provides you
a simple API to call them::

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


Parse response
--------------

MakLogic returns data with multipart/mixed content. To easily extract data, use MLResponseParser class::

   >>> from mlclient import MLResourceClient, MLResponseParser
   >>> config = {
   ...     "host": "localhost",
   ...     "port": 8002,
   ...     "username": "admin",
   ...     "password": "admin",
   ... }
   >>> with MLResourceClient(**config) as client:
   ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
   ...     parsed_resp = MLResponseParser.parse(resp)
   ...     print(parsed_resp)
   ...
   App-Services
