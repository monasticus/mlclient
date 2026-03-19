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

MLClient offers two types of clients to access a MarkLogic Server: high-level and low-level.
High-level clients are designed for specific endpoints, such as ``/v1/documents``.
They provide a simple and intuitive API that covers all the functionality of each endpoint.
Low-level clients are the foundation of MLClient. They use :class:`~mlclient.calls.RestCall` objects to represent the parameters of any endpoint.
You can use low-level clients to send raw requests to the server.
You can learn more about high-level and low-level clients in the following sections.

High-level clients
------------------

High-level clients are designed for specific endpoints of MarkLogic Server and database.
They allow you to manage configuration or documents in MarkLogic with ease.
Each client ensures that you can perform all the operations in the corresponding area.
For example, some of the high-level clients are:

==========================================  ===================
Client                                      Endpoint
==========================================  ===================
:class:`~mlclient.clients.DocumentsClient`  ``/v1/documents``
:class:`~mlclient.clients.EvalClient`       ``/v1/eval``
:class:`~mlclient.clients.LogsClient`       ``/manage/v2/logs``
==========================================  ===================

DocumentsClient
^^^^^^^^^^^^^^^

READ
""""

**Read a document**

.. code-block:: python

    >>> from mlclient import MLManager
    
    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...    doc = docs_client.read("/doc-1.xml")

    >>> doc
    <mlclient.structures.documents.XMLDocument object at 0x7f9200980070>

    >>> doc.doc_type
    <DocumentType.XML: 'xml'>

    >>> doc.uri
    '/doc-1.xml'

    >>> doc.content
    <xml.etree.ElementTree.ElementTree object at 0x7f920095be20>

    >>> doc.content_string
    '''<?xml version="1.0" encoding="UTF-8"?>
    <SomeEntity>
        <ChildNode1>00001</ChildNode1>
        <ChildNode2>888e2050-7148-42c4-b33a-b3dd3505b87b</ChildNode2>
    </SomeEntity>'''

**Read a document as string**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     doc = docs_client.read("/doc-1.xml", output_type=str)

    >>> doc
    <mlclient.structures.documents.RawStringDocument object at 0x7f9200980400>

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

    >>> from mlclient import MLManager

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     doc = docs_client.read("/doc-1.xml", output_type=bytes)

    >>> doc
    <mlclient.structures.documents.RawDocument object at 0x7f9200980490>

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

    >>> from mlclient import MLManager

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     doc = docs_client.read("/doc-1.xml", category=["content", "metadata"])

    >>> doc.metadata
    <mlclient.structures.documents.Metadata object at 0x7f9200980eb0>

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

    >>> from mlclient import MLManager

    >>> uris = [
    ...     "/doc-1.xml",
    ...     "/doc-2.json",
    ...     "/doc-3.xqy",
    ...     "/doc-4.zip",
    ... ]
    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     docs = docs_client.read(uris)

    >>> len(docs)
    4

    >>> xml_doc = next(doc for doc in docs if doc.uri == "/doc-1.xml")
    >>> xml_doc
    <mlclient.structures.documents.XMLDocument object at 0x7f9200920a00>

    >>> json_doc = next(doc for doc in docs if doc.uri == "/doc-2.json")
    >>> json_doc
    <mlclient.structures.documents.JSONDocument object at 0x7f9200920430>

    >>> text_doc = next(doc for doc in docs if doc.uri == "/doc-3.xqy")
    >>> text_doc
    <mlclient.structures.documents.TextDocument object at 0x7f9200920e20>

    >>> bin_doc = next(doc for doc in docs if doc.uri == "/doc-4.zip")
    >>> bin_doc
    <mlclient.structures.documents.BinaryDocument object at 0x7f9200920970>

**Read documents from a custom database**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     doc = docs_client.read("/doc-1.xml", database="App-Services")

    >>> doc
    <mlclient.structures.documents.XMLDocument object at 0x7f92009b4700>


CREATE / UPDATE
"""""""""""""""

**Put a document**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.structures import DocumentFactory

    >>> uri = "/doc-2.json"
    >>> content = {"root": {"child": "data"}}
    >>> doc = DocumentFactory.build_document(uri=uri, content=content)
    >>> doc
    <mlclient.structures.documents.JSONDocument object at 0x7f9200920f70>

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc)
    >>> resp
    {'documents': [{'uri': '/doc-2.json', 'mime-type': 'application/json', 'category': ['metadata', 'content']}]}


**Put a document with metadata**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.structures import DocumentFactory, Metadata

    >>> uri = "/doc-2.json"
    >>> content = {"root": {"child": "data"}}
    >>> metadata = Metadata(collections=["some-collection"])
    >>> doc = DocumentFactory.build_document(uri=uri, content=content, metadata=metadata)

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc)
    >>> resp
    {'documents': [{'uri': '/doc-2.json', 'mime-type': 'application/json', 'category': ['metadata', 'content']}]}


**Put a raw document**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.structures import DocumentFactory, DocumentType

    >>> uri = "/doc-1.xml"
    >>> content = b"<root><child>data</child></root>"
    >>> doc = DocumentFactory.build_raw_document(
    ...     uri=uri,
    ...     content=content,
    ...     doc_type=DocumentType.XML,
    ... )
    >>> doc
    <mlclient.structures.documents.RawDocument object at 0x7f9200929430>

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc)
    >>> resp
    {'documents': [{'uri': '/doc-1.xml', 'mime-type': 'application/xml', 'category': ['metadata', 'content']}]}


**Put a raw document with metadata**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.structures import DocumentFactory, DocumentType

    >>> uri = "/doc-1.xml"
    >>> content = b"<root><child>data</child></root>"
    >>> metadata = b'{"collections": ["some-collection"]}'
    >>> doc = DocumentFactory.build_raw_document(
    ...     uri=uri,
    ...     content=content,
    ...     doc_type=DocumentType.XML,
    ...     metadata=metadata,
    ... )

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc)
    >>> resp
    {'documents': [{'uri': '/doc-1.xml', 'mime-type': 'application/xml', 'category': ['metadata', 'content']}]}

**Put a document to a custom database**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.structures import DocumentFactory

    >>> uri = "/doc-2.json"
    >>> content = {"root": {"child": "data"}}
    >>> doc = DocumentFactory.build_document(uri=uri, content=content)
    >>> doc
    <mlclient.structures.documents.JSONDocument object at 0x7f9200920f70>

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc, database="Documents")
    >>> resp
    {'documents': [{'uri': '/doc-2.json', 'mime-type': 'application/json', 'category': ['metadata', 'content']}]}

**Update document's metadata**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.structures import Metadata, MetadataDocument

    >>> uri = "/doc-2.json"
    >>> metadata = Metadata(collections=["some-collection"])
    >>> doc = MetadataDocument(uri, metadata)
    >>> doc
    <mlclient.structures.documents.MetadataDocument object at 0x7f9200929e20>

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc)
    >>> resp
    {'documents': [{'uri': '/doc-2.json', 'mime-type': '', 'category': ['metadata']}]}


**Put multiple documents**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.structures import DocumentFactory, DocumentType
    
    >>> uri_1 = "/doc-1.xml"
    >>> content_1 = b"<root><child>data</child></root>"
    >>> doc_1 = DocumentFactory.build_raw_document(
    ...     uri=uri_1,
    ...     content=content_1,
    ...     doc_type=DocumentType.XML,
    ... )

    >>> uri_2 = "/doc-2.json"
    >>> content_2 = {"root": {"child": "data"}}
    >>> doc_2 = DocumentFactory.build_document(uri=uri_2, content=content_2)
    

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create([doc_1, doc_2])
    >>> resp
    {'documents': [{'uri': '/doc-1.xml', 'mime-type': 'application/xml', 'category': ['metadata', 'content']}, {'uri': '/doc-2.json', 'mime-type': 'application/json', 'category': ['metadata', 'content']}]}


**Put documents with default metadata**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.structures import DocumentFactory, DocumentType, Metadata
    
    >>> default_metadata = Metadata(collections=["some-collection"])
    
    >>> uri_1 = "/doc-1.xml"
    >>> content_1 = b"<root><child>data</child></root>"
    >>> doc_1 = DocumentFactory.build_raw_document(
    ...     uri=uri_1,
    ...     content=content_1,
    ...     doc_type=DocumentType.XML,
    ... )

    >>> uri_2 = "/doc-2.json"
    >>> content_2 = {"root": {"child": "data"}}
    >>> doc_2 = DocumentFactory.build_document(uri=uri_2, content=content_2)
    

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create([default_metadata, doc_1, doc_2])
    >>> resp
    {'documents': [{'uri': '/doc-1.xml', 'mime-type': 'application/xml', 'category': ['metadata', 'content']}, {'uri': '/doc-2.json', 'mime-type': 'application/json', 'category': ['metadata', 'content']}]}


DELETE
""""""

**Delete a document**

.. code-block:: python

    >>> from mlclient import MLManager
    
    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     docs_client.delete("/doc-1.xml")


**Delete multiple documents**

.. code-block:: python

    >>> from mlclient import MLManager
    
    >>> uris = [
    ...     "/doc-1.xml",
    ...     "/doc-2.json",
    ...     "/doc-3.xqy",
    ...     "/doc-4.zip",
    ... ]
    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     docs_client.delete(uris)


**Delete a document from a custom database**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     docs_client.delete("/doc-1.xml", database="Documents")


**Delete document's metadata**

.. code-block:: python

    >>> from mlclient import MLManager
    
    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     docs_client.delete("/doc-1.xml", category=["properties", "collections"])


**Delete a temporal document**

.. code-block:: python

    >>> from mlclient import MLManager
    
    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     docs_client.delete("/doc-1.xml", temporal_collection="temporal-collection")


**Wipe a temporal document**

.. code-block:: python

    >>> from mlclient import MLManager
    
    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     docs_client.delete(
    ...        "/doc-1.xml",
    ...        temporal_collection="temporal-collection",
    ...        wipe_temporal=True,
    ... )


EvalClient
^^^^^^^^^^

**Evaluate code from a file**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> manager = MLManager("local")
    >>> with manager.get_eval_client() as client:
    ...     result = client.eval("./xqy-code-to-eval.xqy)
    ...     result = client.eval("./js-code-to-eval.js)


**Evaluate raw xquery code**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_eval_client() as client:
    ...     result = client.eval(xq="fn:current-dateTime()")
    >>> result
    datetime.datetime(2024, 2, 22, 11, 38, 32, 709484, tzinfo=datetime.timezone.utc)


**Evaluate raw javascript code**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_eval_client() as client:
    ...     result = client.eval(js="fn.currentDateTime()")
    >>> result
    datetime.datetime(2024, 2, 22, 11, 39, 22, 264102, tzinfo=datetime.timezone.utc)


**Evaluate code with variables**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> xq = '''
    ... declare variable $DAYS external;
    ...
    ... fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'''

    >>> with MLManager("local").get_eval_client() as client:
    ...     result = client.eval(
    ...         xq=xq,
    ...         variables={"DAYS": 5},
    ...     )
    >>> result
    datetime.datetime(2024, 2, 17, 12, 17, 49, 556376, tzinfo=datetime.timezone.utc)


.. code-block:: python

    >>> from mlclient import MLManager

    >>> xq = '''
    ... declare variable $DAYS external;
    ...
    ... fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'''

    >>> with MLManager("local").get_eval_client() as client:
    ...     result = client.eval(
    ...         xq=xq,
    ...         DAYS=5,
    ...     )
    >>> result
    datetime.datetime(2024, 2, 17, 12, 19, 45, 225135, tzinfo=datetime.timezone.utc)


**Evaluate code with variables within a namespace**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> xq = '''
    ... declare variable $local:DAYS external;
    ...
    ... fn:current-dateTime() - xs:dayTimeDuration("P" || $local:DAYS || "D")'''

    >>> with MLManager("local").get_eval_client() as client:
    ...     result = client.eval(
    ...         xq=xq,
    ...         variables={
    ...             "{http://www.w3.org/2005/xquery-local-functions}DAYS": 5,
    ...         },
    ...     )
    >>> result
    datetime.datetime(2024, 2, 17, 12, 21, 28, 547853, tzinfo=datetime.timezone.utc)


**Evaluate code on a custom database**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_eval_client() as client:
    ...     result = client.eval(
    ...         xq="xdmp:database() => xdmp:database-name()",
    ...         database="Documents",
    ...     )
    >>> result
    'Documents'


**Evaluate code and get raw data**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_eval_client() as client:
    ...     result = client.eval(xq="fn:current-dateTime()", output_type=str)
    >>> result
    '2024-02-22T12:24:40.362014Z'


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_eval_client() as client:
    ...     result = client.eval(xq="fn:current-dateTime()", output_type=bytes)
    >>> result
    b'2024-02-22T12:24:53.677793Z'


LogsClient
^^^^^^^^^^

Get all logs
""""""""""""

*8002_ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002)
    >>> list(logs)[0]
    {'timestamp': '2024-01-09T13:30:51.187Z', 'level': 'error', 'message': 'Test Log 1'}


.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.clients import LogType

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, log_type=LogType.ERROR)
    >>> list(logs)[0]
    {'timestamp': '2024-01-09T13:30:51.187Z', 'level': 'error', 'message': 'Test Log 1'}


*8002_AccessLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.clients import LogType

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, log_type=LogType.ACCESS)
    >>> list(logs)[0]
    {'message': '172.17.0.1 - - [22/Feb/2024:12:13:18 +0000] "POST /v1/eval HTTP/1.1" 401 209 - "python-httpx/0.27.0"'}



*8002_RequestLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.clients import LogType

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, log_type=LogType.REQUEST)
    >>> list(logs)[0]
    {'message': '{"time":"2024-02-22T12:38:27Z", "url":"/manage/v2/logs?format=json", "user":"admin", "elapsedTime":1.801654, "requests":1, "valueCacheHits":5743, "valueCacheMisses":349701, "regexpCacheHits":5278, "regexpCacheMisses":10, "fsProgramCacheMisses":1, "fsMainModuleSequenceCacheMisses":1, "fsLibraryModuleCacheMisses":226, "compileTime":0.757087, "runTime":1.043248}'}


*ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs()


*TaskServer_ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server="TaskServer")


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=0)


Get limited logs
""""""""""""""""

**Time frames**

.. note::

    ``start_time``, ``end_time`` and ``regex`` arguments work only for error logs


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, start_time="10:00")


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, end_time="12:00")


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(
    ...         app_server=8002,
    ...         start_time="10:00",
    ...         end_time="12:00",
    ...     )


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(
    ...         app_server=8002,
    ...         start_time="2024-02-01",
    ...         end_time="2024-02-03",
    ...     )


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(
    ...         app_server=8002,
    ...         start_time="2024-02-01 10:00",
    ...         end_time="2024-02-03",
    ...     )


**RegEx**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, regex="Forest Meters")


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, regex="Forest M.*")


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, regex="Memory [^1]{1,2}%")


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(
    ...         app_server=8002,
    ...         start_time="2024-02-01",
    ...         end_time="2024-02-03",
    ...         regex="Memory [^1]{1,2}%",
    ...     )


Low-level clients
-----------------

Low-level clients offer a basic HTTP client functionality that is compatible with MarkLogic Server configuration.
They also work with :class:`~mlclient.calls.RestCall` objects, which are python representations of MarkLogic resources’ calls.
You can use low-level clients to send customized requests that are not supported by the high-level client API,
or to handle the responses yourself.
Moreover, you can customize low-level clients to implement python api for your own resources.

====================================  =======================================================================================================================================================
Client                                Description
====================================  =======================================================================================================================================================
:class:`~mlclient.MLClient`           The lowest level client that accepts ML configuration and sends HTTP requests
:class:`~mlclient.MLResourceClient`   A client that provides an additional :meth:`~mlclient.MLResourceClient.call` method that works with :class:`~mlclient.calls.RestCall` objects
:class:`~mlclient.MLResourcesClient`  A facade client that offers methods for all :class:`~mlclient.RestCall` implementations (and thus all ML Resources endpoints)
====================================  =======================================================================================================================================================

MLClient
^^^^^^^^

The lowest level client that accepts ML configuration and sends HTTP requests.

Internally, ``MLClient`` uses ``httpx``. Its default retry strategy is intentionally
conservative: transport-level retries are enabled for idempotent methods only.
If you need a different policy, pass a custom ``retry`` strategy when initializing
the client.

MLClient also exposes the standard MarkLogic endpoint ports as public constants:

- ``MARKLOGIC_REST_API_PORT`` = ``8000``
- ``MARKLOGIC_ADMIN_API_PORT`` = ``8001``
- ``MARKLOGIC_MANAGE_API_PORT`` = ``8002``

Two retry presets are also exported:

- ``DEFAULT_RETRY_STRATEGY`` for normal requests
- ``RESTART_RETRY_STRATEGY`` for Admin timestamp polling during restart windows

Connection
""""""""""

The easiest way to start a connection is to initialize :class:`~mlclient.MLClient` as a context manager:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     resp = client.get("/manage/v2/servers")


If you would like to explicitly connect and disconnect a client, however, you can do it as below:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> client = MLClient()
    >>> client.connect()
    >>> resp = client.get("/manage/v2/servers")
    >>> client.disconnect()


To check if a client is connected you can use :meth:`~mlclient.MLClient.is_connected` method:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> client = MLClient()
    >>> client.connect()
    >>> client.is_connected()
    True
    >>> client.disconnect()
    >>> client.is_connected()
    False


GET request
"""""""""""

*A simple GET request*

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     resp = client.get("/manage/v2/servers")


*Custom parameters and headers*

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     resp = client.get(
    ...         "/manage/v2/servers",
    ...         params={"format": "json"},
    ...         headers={"custom-header": "custom-value"},
    ...     )


POST request
""""""""""""

*A simple POST request*

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     resp = client.post(
    ...         "/manage/v2/databases",
    ...         body={"database-name": "CustomDatabase"},
    ...     )


*Custom parameters and headers*

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     resp = client.post(
    ...         "/v1/eval",
    ...         body={"xquery": "fn:current-dateTime()"},
    ...         params={"database": "Documents"},
    ...         headers={"Content-Type": "application/x-www-form-urlencoded"},
    ...     )


PUT request
"""""""""""

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     resp = client.put(
    ...         "/manage/v2/databases/CustomDatabase/properties",
    ...         body={"enabled": False},
    ...         headers={"Content-Type": "application/json"}
    ...     )


DELETE request
""""""""""""""

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     resp = client.delete(
    ...         "/manage/v2/databases/CustomDatabase",
    ...         params={"forest-delete": "configuration"}
    ...     )


Restart readiness
"""""""""""""""""

Some Management and Admin API operations return ``202 Accepted`` together with
``Location: /admin/v1/timestamp`` and a ``restart`` payload body. That payload
contains one or more ``last-startup`` entries keyed by ``host-id``. This
indicates that MarkLogic accepted the request and that callers should verify
readiness through the Admin timestamp endpoint on port ``8001`` before issuing
follow-up administrative requests.

The timestamp endpoint is host-specific, not cluster-wide. MarkLogic
documentation explicitly notes that if an operation restarts multiple hosts,
the caller must iterate through the returned ``host-id`` and timestamp pairs
and check each host separately. ``MLClient.wait_for_restart_completion()``
does that internally: for multi-host restart responses it resolves host ids
through ``GET /manage/v2/hosts`` and waits for all affected hosts in parallel.
The current client host is probed immediately while the host mapping request is
in flight, and the remaining host probes are started as soon as the mapping is
available. If the current client host is one of the affected hosts, the method
still waits for a timestamp newer than that host's own ``last-startup`` value
before it returns.

Use :meth:`~mlclient.MLClient.wait_for_restart_completion` for this check:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     resp = client.delete_(
    ...         "/manage/v2/servers/TestServer",
    ...         params={"group-id": "Default"},
    ...     )
    ...     client.wait_for_restart_completion(resp)

If you call :meth:`~mlclient.MLClient.wait_for_restart_completion` without a
response, it performs a single readiness probe using a retry policy tuned for
restart windows:

.. code-block:: python

    >>> from mlclient import MLClient

    >>> with MLClient() as client:
    ...     client.wait_for_restart_completion()

For multi-host restart responses, the method waits for all affected hosts
before it returns.


MLResourceClient
^^^^^^^^^^^^^^^^


MLResourcesClient
^^^^^^^^^^^^^^^^^
