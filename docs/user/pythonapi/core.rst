====
Core
====

.. contents::
   :local:
   :backlinks: top
   :depth: 3

Clients
=======

Overview
--------

MLClient offers a layered architecture to access a MarkLogic Server: high-level services, mid-level API clients, and a low-level HTTP client.
High-level services are designed for specific endpoints, such as ``/v1/documents``.
They provide a simple and intuitive API that covers all the functionality of each endpoint.
The mid-level layer provides three API clients that mirror MarkLogic's API tiers:
:class:`~mlclient.api.RestApi` for ``/v1/*`` endpoints, :class:`~mlclient.api.ManageApi` for ``/manage/v2/*`` (port 8002), and :class:`~mlclient.api.AdminApi` for ``/admin/v1/*`` (port 8001).
Each uses :class:`~mlclient.calls.ApiCall` objects to represent the parameters of any endpoint.
The low-level :class:`~mlclient.HttpClient` lets you send raw HTTP requests to the server.
You can learn more about services and clients in the following sections.

Every layer is also available asynchronously through :class:`~mlclient.AsyncMLClient`,
which mirrors :class:`~mlclient.MLClient` 1:1. All methods become coroutines -
just use ``async with AsyncMLClient() as ml:`` and ``await`` on each call.
The same applies to the mid-level clients: :class:`~mlclient.api.AsyncRestApi`,
:class:`~mlclient.api.AsyncManageApi`, :class:`~mlclient.api.AsyncAdminApi`,
and to the low-level :class:`~mlclient.AsyncHttpClient`.

MLClient
--------

:class:`~mlclient.MLClient` is the main entry point that provides layered access to MarkLogic
through ``.http``, ``.rest``, ``.manage``, ``.admin``, and service properties.

====================================  =======================================================================================================================================================
Layer                                 Description
====================================  =======================================================================================================================================================
:class:`~mlclient.MLClient`           Main entry point with layered access (``.http``, ``.rest``, ``.manage``, ``.admin``, ``.documents``, ``.eval``, ``.logs``)
:class:`~mlclient.AsyncMLClient`      Async variant of ``MLClient`` - same API, all methods are coroutines
:class:`~mlclient.HttpClient`         Low-level HTTP client that accepts ML configuration and sends raw HTTP requests
:class:`~mlclient.AsyncHttpClient`    Async variant of ``HttpClient``
:class:`~mlclient.ApiClient`          Mid-level client providing :meth:`~mlclient.ApiClient.call` for :class:`~mlclient.calls.ApiCall` objects
:class:`~mlclient.AsyncApiClient`     Async variant of ``ApiClient``
====================================  =======================================================================================================================================================

Internally, the underlying ``HttpClient`` uses ``httpx``. Its default retry strategy is intentionally
conservative: transport-level retries are enabled for idempotent methods only.
If you need a different policy, pass a custom ``retry`` strategy when initializing
the client.

``HttpClient`` also exposes the standard MarkLogic endpoint ports as public constants:

- ``MARKLOGIC_REST_API_PORT`` = ``8000``
- ``MARKLOGIC_ADMIN_API_PORT`` = ``8001``
- ``MARKLOGIC_MANAGE_API_PORT`` = ``8002``

Two retry presets are also exported:

- ``DEFAULT_RETRY_STRATEGY`` for normal requests
- ``RESTART_RETRY_STRATEGY`` for Admin timestamp polling during restart windows

Connection
^^^^^^^^^^

The easiest way to start a connection is to initialize :class:`~mlclient.MLClient` as a context manager:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.http.get("/manage/v2/servers")


If you would like to explicitly connect and disconnect a client, however, you can do it as below:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> ml = MLClient()
    >>> ml.connect()
    >>> resp = ml.http.get("/manage/v2/servers")
    >>> ml.disconnect()


Async connection
""""""""""""""""

:class:`~mlclient.AsyncMLClient` follows the same pattern with ``async with``:

.. code-block:: python

    >>> from mlclient import AsyncMLClient

    >>> async with AsyncMLClient() as ml:
    ...     resp = await ml.http.get("/manage/v2/servers")


To check if a client is connected you can use :meth:`~mlclient.MLClient.is_connected` method:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> ml = MLClient()
    >>> ml.connect()
    >>> ml.is_connected()
    True
    >>> ml.disconnect()
    >>> ml.is_connected()
    False


API tiers and port routing
^^^^^^^^^^^^^^^^^^^^^^^^^^

MarkLogic exposes three separate HTTP API tiers, each bound to a fixed port:

========================  ===========  ===========================
Tier                      Port         Endpoints
========================  ===========  ===========================
Client (REST) API         8000/custom  ``/v1/*``
Admin API                 8001         ``/admin/v1/*``
Management API            8002         ``/manage/v2/*``
========================  ===========  ===========================

Port 8000 is the default App-Services REST server. Custom REST app servers
(created via the Management API) also serve ``/v1/*`` on their configured port.
Neither custom HTTP nor custom REST app servers serve ``/manage/v2/*`` or
``/admin/v1/*`` endpoints - those are only available on the fixed ports shown above.
Port 8000 appears to accept ``/manage/v2/*`` requests, but it silently redirects
them to port 8002.

``MLClient`` reflects this topology through three API properties:

.. code-block:: text

    MLClient (main entry point)
      +- .http       -> HttpClient   (raw HTTP on the main port)
      +- .rest       -> RestApi      (/v1/* on the main port)
      +- .manage     -> ManageApi    (/manage/v2/* on port 8002)
      +- .admin      -> AdminApi     (/admin/v1/* on port 8001)
      +- .parser     -> MLResponseParser
      +- .documents, .eval, .logs -> high-level services

Port routing is automatic. When the main ``port`` is already 8002 (the default),
``.manage`` reuses the same HTTP connection. Otherwise, a separate connection to
port 8002 is lazily created on first access. The same logic applies to
``.admin`` and port 8001. All secondary connections share the same ``protocol``,
``host``, ``auth_method``, ``username``, and ``password`` as the main client.
They are also managed by the ``connect()`` / ``disconnect()`` lifecycle.

.. code-block:: python

    >>> from mlclient import MLClient

    # Default port is 8002 - .manage reuses the connection, .admin creates one to 8001
    >>> with MLClient() as ml:
    ...     resp = ml.manage.databases.get_list()
    ...     ts = ml.admin.get_timestamp()

    # Custom REST server on port 8040 - .rest uses 8040, .manage/admin use 8002/8001
    >>> with MLClient(port=8040) as ml:
    ...     resp = ml.rest.eval.post(xquery="1")
    ...     dbs = ml.manage.databases.get_list()


High-level services
-------------------

High-level services are designed for specific endpoints of MarkLogic Server and database.
They allow you to manage configuration or documents in MarkLogic with ease.
Each service ensures that you can perform all the operations in the corresponding area.
For example, some of the high-level services are:

==========================================  ===================
Service                                     Endpoint
==========================================  ===================
``ml.documents``                            ``/v1/documents``
``ml.eval``                                 ``/v1/eval``
``ml.logs``                                 ``/manage/v2/logs``
==========================================  ===================

DocumentsService
^^^^^^^^^^^^^^^^

READ
""""

**Read a document**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...    doc = ml.documents.read("/doc-1.xml")

    >>> doc.uri
    '/doc-1.xml'

    >>> doc.doc_type
    <DocumentType.XML: 'xml'>

    >>> doc.content_string
    '''<?xml version="1.0" encoding="UTF-8"?>
    <SomeEntity>
        <ChildNode1>00001</ChildNode1>
        <ChildNode2>888e2050-7148-42c4-b33a-b3dd3505b87b</ChildNode2>
    </SomeEntity>'''

**Read a document as string**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     doc = ml.documents.read("/doc-1.xml", output_type=str)

    >>> doc.doc_type
    <DocumentType.XML: 'xml'>

    >>> doc.content
    '''<?xml version="1.0" encoding="UTF-8"?>
    <SomeEntity>
        <ChildNode1>00001</ChildNode1>
        <ChildNode2>888e2050-7148-42c4-b33a-b3dd3505b87b</ChildNode2>
    </SomeEntity>'''

**Read a document as bytes**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     doc = ml.documents.read("/doc-1.xml", output_type=bytes)

    >>> doc.doc_type
    <DocumentType.XML: 'xml'>

    >>> doc.content
    b'''<?xml version="1.0" encoding="UTF-8"?>
    <SomeEntity>
        <ChildNode1>00001</ChildNode1>
        <ChildNode2>888e2050-7148-42c4-b33a-b3dd3505b87b</ChildNode2>
    </SomeEntity>'''

**Read a document with metadata**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     doc = ml.documents.read("/doc-1.xml", category=["content", "metadata"])

    >>> doc.metadata.to_json()
    {'collections': [], 'permissions': [], 'properties': {}, 'quality': 0, 'metadataValues': {}}

    >>> doc.metadata.to_xml_string(indent=4)
    '''<?xml version=\'1.0\' encoding=\'utf-8\'?>
    <?xml version="1.0" encoding="utf-8"?>
    <rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">
        <rapi:collections/>
        <rapi:permissions/>
        <prop:properties xmlns:prop="http://marklogic.com/xdmp/property"/>
        <rapi:quality>0</rapi:quality>
        <rapi:metadata-values/>
    </rapi:metadata>
    '''

**Read multiple documents**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     docs = ml.documents.read(
    ...         ["/doc-1.xml", "/doc-2.json", "/doc-3.xqy", "/doc-4.zip"]
    ...     )

    >>> len(docs)
    4

    >>> docs["/doc-1.xml"]
    <mlclient.models.documents.XMLDocument object at 0x7f9200920a00>

    >>> docs["/doc-2.json"]
    <mlclient.models.documents.JSONDocument object at 0x7f9200920430>

    >>> docs["/doc-3.xqy"]
    <mlclient.models.documents.TextDocument object at 0x7f9200920e20>

    >>> docs["/doc-4.zip"]
    <mlclient.models.documents.BinaryDocument object at 0x7f9200920970>

**Read documents from a custom database**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     doc = ml.documents.read("/doc-1.xml", database="App-Services")


WRITE (create / update)
"""""""""""""""""""""""

**Put a document**

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.models import Document

    >>> doc = Document.create("/doc-2.json", {"root": {"child": "data"}})
    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.write(doc)


**Put a document with metadata**

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.models import Document, Metadata

    >>> metadata = Metadata(collections=["some-collection"])
    >>> doc = Document.create(
    ...     "/doc-2.json",
    ...     {"root": {"child": "data"}},
    ...     metadata=metadata,
    ... )

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.write(doc)


**Put a raw document**

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.models import Document, DocumentType

    >>> doc = Document.create_raw(
    ...     "/doc-1.xml",
    ...     b"<root><child>data</child></root>",
    ...     doc_type=DocumentType.XML,
    ... )
    >>> doc
    <mlclient.models.documents.RawDocument object at 0x7f9200929430>

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.write(doc)


**Put a raw document with metadata**

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.models import Document, DocumentType

    >>> doc = Document.create_raw(
    ...     "/doc-1.xml",
    ...     b"<root><child>data</child></root>",
    ...     doc_type=DocumentType.XML,
    ...     metadata=b'{"collections": ["some-collection"]}',
    ... )

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.write(doc)


**Put a document to a custom database**

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.models import Document

    >>> doc = Document.create("/doc-2.json", {"root": {"child": "data"}})
    >>> doc
    <mlclient.models.documents.JSONDocument object at 0x7f9200920f70>

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.write(doc, database="Documents")


**Update document's metadata**

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.models import Metadata, MetadataDocument

    >>> metadata = Metadata(collections=["some-collection"])
    >>> doc = MetadataDocument("/doc-2.json", metadata)
    >>> doc
    <mlclient.models.documents.MetadataDocument object at 0x7f9200929e20>

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.write(doc)


**Put multiple documents**

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.models import Document, DocumentType

    >>> doc_1 = Document.create_raw(
    ...     "/doc-1.xml",
    ...     b"<root><child>data</child></root>",
    ...     doc_type=DocumentType.XML,
    ... )
    >>> doc_2 = Document.create("/doc-2.json", {"root": {"child": "data"}})

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.write([doc_1, doc_2])


**Put documents with default metadata**

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.models import Document, DocumentType, Metadata

    >>> default_metadata = Metadata(collections=["some-collection"])
    >>> doc_1 = Document.create_raw(
    ...     "/doc-1.xml",
    ...     b"<root><child>data</child></root>",
    ...     doc_type=DocumentType.XML,
    ... )
    >>> doc_2 = Document.create("/doc-2.json", {"root": {"child": "data"}})


    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.write([default_metadata, doc_1, doc_2])


DELETE
""""""

**Delete a document**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.delete("/doc-1.xml")


**Delete multiple documents**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.delete(
    ...         ["/doc-1.xml", "/doc-2.json", "/doc-3.xqy", "/doc-4.zip"]
    ...     )


**Delete a document from a custom database**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.delete("/doc-1.xml", database="Documents")


**Delete document's metadata**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.delete("/doc-1.xml", category=["properties", "collections"])


**Delete a temporal document**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.delete("/doc-1.xml", temporal_collection="temporal-collection")


**Wipe a temporal document**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client("app-services") as ml:
    ...     ml.documents.delete(
    ...        "/doc-1.xml",
    ...        temporal_collection="temporal-collection",
    ...        wipe_temporal=True,
    ... )


EvalService
^^^^^^^^^^^

**Evaluate code from a file**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> mgr = MLClientManager("local")
    >>> with mgr.get_client() as ml:
    ...     result1 = ml.eval.file("./xqy-code-to-eval.xqy")
    ...     result2 = ml.eval.file("./js-code-to-eval.js")


**Evaluate raw xquery code**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     result = ml.eval.xquery("fn:current-dateTime()")
    >>> result
    datetime.datetime(2024, 2, 22, 11, 38, 32, 709484, tzinfo=datetime.timezone.utc)


**Evaluate raw javascript code**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     result = ml.eval.javascript("fn.currentDateTime()")
    >>> result
    datetime.datetime(2024, 2, 22, 11, 39, 22, 264102, tzinfo=datetime.timezone.utc)


**Evaluate code with variables**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> xq = '''
    ... declare variable $DAYS external;
    ...
    ... fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'''

    >>> with MLClientManager("local").get_client() as ml:
    ...     result = ml.eval.xquery(
    ...         xq,
    ...         variables={"DAYS": 5},
    ...     )
    >>> result
    datetime.datetime(2024, 2, 17, 12, 17, 49, 556376, tzinfo=datetime.timezone.utc)


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> xq = '''
    ... declare variable $DAYS external;
    ...
    ... fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'''

    >>> with MLClientManager("local").get_client() as ml:
    ...     result = ml.eval.xquery(
    ...         xq,
    ...         DAYS=5,
    ...     )
    >>> result
    datetime.datetime(2024, 2, 17, 12, 19, 45, 225135, tzinfo=datetime.timezone.utc)


**Evaluate code with variables within a namespace**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> xq = '''
    ... declare variable $local:DAYS external;
    ...
    ... fn:current-dateTime() - xs:dayTimeDuration("P" || $local:DAYS || "D")'''

    >>> with MLClientManager("local").get_client() as ml:
    ...     result = ml.eval.xquery(
    ...         xq,
    ...         variables={
    ...             "{http://www.w3.org/2005/xquery-local-functions}DAYS": 5,
    ...         },
    ...     )
    >>> result
    datetime.datetime(2024, 2, 17, 12, 21, 28, 547853, tzinfo=datetime.timezone.utc)


**Evaluate code on a custom database**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     result = ml.eval.xquery(
    ...         "xdmp:database() => xdmp:database-name()",
    ...         database="Documents",
    ...     )
    >>> result
    'Documents'


**Evaluate code and get raw data**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     result = ml.eval.xquery("fn:current-dateTime()", output_type=str)
    >>> result
    '2024-02-22T12:24:40.362014Z'


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     result = ml.eval.xquery("fn:current-dateTime()", output_type=bytes)
    >>> result
    b'2024-02-22T12:24:53.677793Z'


LogsService
^^^^^^^^^^^

Get all logs
""""""""""""

*8002_ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002)
    >>> list(logs)[0]
    {'timestamp': '2024-01-09T13:30:51.187Z', 'level': 'error', 'message': 'Test Log 1'}

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.services import LogType

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, LogType.ERROR)
    >>> list(logs)[0]
    {'timestamp': '2024-01-09T13:30:51.187Z', 'level': 'error', 'message': 'Test Log 1'}


.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.services import LogType

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, "error")
    >>> list(logs)[0]
    {'timestamp': '2024-01-09T13:30:51.187Z', 'level': 'error', 'message': 'Test Log 1'}


*8002_AccessLog.txt*

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.services import LogType

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, LogType.ACCESS)
    >>> list(logs)[0]
    {'message': '172.17.0.1 - - [22/Feb/2024:12:13:18 +0000] "POST /v1/eval HTTP/1.1" 401 209 - "python-httpx/0.27.0"'}


.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.services import LogType

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, "access")
    >>> list(logs)[0]
    {'message': '172.17.0.1 - - [22/Feb/2024:12:13:18 +0000] "POST /v1/eval HTTP/1.1" 401 209 - "python-httpx/0.27.0"'}


*8002_RequestLog.txt*

.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.services import LogType

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, LogType.REQUEST)
    >>> list(logs)[0]
    {'message': '{"time":"2024-02-22T12:38:27Z", "url":"/manage/v2/logs?format=json", "user":"admin", "elapsedTime":1.801654, "requests":1, "valueCacheHits":5743, "valueCacheMisses":349701, "regexpCacheHits":5278, "regexpCacheMisses":10, "fsProgramCacheMisses":1, "fsMainModuleSequenceCacheMisses":1, "fsLibraryModuleCacheMisses":226, "compileTime":0.757087, "runTime":1.043248}'}


.. code-block:: python

    >>> from mlclient import MLClientManager
    >>> from mlclient.services import LogType

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, "request")
    >>> list(logs)[0]
    {'message': '{"time":"2024-02-22T12:38:27Z", "url":"/manage/v2/logs?format=json", "user":"admin", "elapsedTime":1.801654, "requests":1, "valueCacheHits":5743, "valueCacheMisses":349701, "regexpCacheHits":5278, "regexpCacheMisses":10, "fsProgramCacheMisses":1, "fsMainModuleSequenceCacheMisses":1, "fsLibraryModuleCacheMisses":226, "compileTime":0.757087, "runTime":1.043248}'}


*ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get()


*TaskServer_ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get("TaskServer")


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(0)


Get limited logs
""""""""""""""""

**Time frames**

.. note::

    ``start_time``, ``end_time`` and ``regex`` arguments work only for error logs


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, start_time="10:00")


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, end_time="12:00")


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(
    ...         8002,
    ...         start_time="10:00",
    ...         end_time="12:00",
    ...     )


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(
    ...         8002,
    ...         start_time="2024-02-01",
    ...         end_time="2024-02-03",
    ...     )


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(
    ...         8002,
    ...         start_time="2024-02-01 10:00",
    ...         end_time="2024-02-03",
    ...     )


**RegEx**

.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, regex="Forest Meters")


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, regex="Forest M.*")


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(8002, regex="Memory [^1]{1,2}%")


.. code-block:: python

    >>> from mlclient import MLClientManager

    >>> with MLClientManager("local").get_client() as ml:
    ...     logs = ml.logs.get(
    ...         8002,
    ...         start_time="2024-02-01",
    ...         end_time="2024-02-03",
    ...         regex="Memory [^1]{1,2}%",
    ...     )


Mid-level API clients
---------------------

Below the high-level services, MLClient exposes three mid-level API clients that correspond
to MarkLogic's API tiers. They work with :class:`~mlclient.calls.ApiCall` objects, which are
python representations of MarkLogic endpoint calls. You can use these clients to send
customized requests that are not supported by the high-level service API, or to handle the
responses yourself.

RestApi
^^^^^^^

:class:`~mlclient.api.RestApi` provides access to ``/v1/*`` endpoints on the main port.

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.rest.eval.post(
    ...         xquery="xdmp:database() => xdmp:database-name()",
    ...     )
    ...     parsed = ml.parser.parse(resp)
    ...     print(parsed)
    ...
    App-Services

ManageApi
^^^^^^^^^
:class:`~mlclient.api.ManageApi` provides access to ``/manage/v2/*`` endpoints on port 8002.

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.manage.databases.get_properties(
    ...         "Documents", data_format="json",
    ...     )
    ...     print(resp.json()["database-name"])
    ...
    Documents

AdminApi
^^^^^^^^

:class:`~mlclient.api.AdminApi` provides access to ``/admin/v1/*`` endpoints on port 8001.

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.admin.get_timestamp()
    ...     print(resp.text)
    ...
    2024-06-21T14:08:32.130813Z


Low-level HTTP
--------------

The low-level :class:`~mlclient.HttpClient` lets you send raw HTTP requests.
It is accessible via ``ml.http``.

GET request
^^^^^^^^^^^

*A simple GET request*

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.http.get("/manage/v2/servers")


*Custom parameters and headers*

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.http.get(
    ...         "/manage/v2/servers",
    ...         params={"format": "json"},
    ...         headers={"custom-header": "custom-value"},
    ...     )


POST request
^^^^^^^^^^^^

*A simple POST request*

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.http.post(
    ...         "/manage/v2/databases",
    ...         {"database-name": "CustomDatabase"},
    ...     )


*Custom parameters and headers*

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.http.post(
    ...         "/v1/eval",
    ...         {"xquery": "fn:current-dateTime()"},
    ...         params={"database": "Documents"},
    ...         headers={"Content-Type": "application/x-www-form-urlencoded"},
    ...     )


PUT request
^^^^^^^^^^^

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.http.put(
    ...         "/manage/v2/databases/CustomDatabase/properties",
    ...         {"enabled": False},
    ...         headers={"Content-Type": "application/json"}
    ...     )


DELETE request
^^^^^^^^^^^^^^

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.http.delete(
    ...         "/manage/v2/databases/CustomDatabase",
    ...         params={"forest-delete": "configuration"}
    ...     )


Restart readiness
-----------------

Some Management and Admin API operations return ``202 Accepted`` together with
``Location: /admin/v1/timestamp`` and a ``restart`` payload body. That payload
contains one or more ``last-startup`` entries keyed by ``host-id``. This
indicates that MarkLogic accepted the request and that callers should verify
readiness through the Admin timestamp endpoint on port ``8001`` before issuing
follow-up administrative requests.

The timestamp endpoint is host-specific, not cluster-wide. MarkLogic
documentation explicitly notes that if an operation restarts multiple hosts,
the caller must iterate through the returned ``host-id`` and timestamp pairs
and check each host separately. ``MLClient.wait_for_restart()``
does that internally: for multi-host restart responses it resolves host ids
through ``GET /manage/v2/hosts`` and waits for all affected hosts in parallel.
The current client host is probed immediately while the host mapping request is
in flight, and the remaining host probes are started as soon as the mapping is
available. If the current client host is one of the affected hosts, the method
still waits for a timestamp newer than that host's own ``last-startup`` value
before it returns.

Use :meth:`~mlclient.MLClient.wait_for_restart` for this check:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     resp = ml.http.delete(
    ...         "/manage/v2/servers/TestServer",
    ...         params={"group-id": "Default"},
    ...     )
    ...     ml.wait_for_restart(resp)

If you call :meth:`~mlclient.MLClient.wait_for_restart` without a
response, it performs a single readiness probe using a retry policy tuned for
restart windows:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as ml:
    ...     ml.wait_for_restart()

For multi-host restart responses, the method waits for all affected hosts
before it returns.
