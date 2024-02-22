====
Core
====

Clients
=======

Overview
--------

MLClient offers two types of clients to access a MarkLogic Server: high-level and low-level.
High-level clients are designed for specific endpoints, such as ``/v1/documents``.
They provide a simple and intuitive API that covers all the functionality of each endpoint.
Low-level clients are the foundation of MLClient. They use :class:`~mlclient.calls.ResourceCall` objects to represent the parameters of any endpoint.
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
    <mlclient.model.data.XMLDocument object at 0x7f9200980070>

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
    <mlclient.model.data.RawStringDocument object at 0x7f9200980400>

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
    <mlclient.model.data.RawDocument object at 0x7f9200980490>

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
    <mlclient.model.data.Metadata object at 0x7f9200980eb0>

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
    <mlclient.model.data.XMLDocument object at 0x7f9200920a00>

    >>> json_doc = next(doc for doc in docs if doc.uri == "/doc-2.json")
    >>> json_doc
    <mlclient.model.data.JSONDocument object at 0x7f9200920430>

    >>> text_doc = next(doc for doc in docs if doc.uri == "/doc-3.xqy")
    >>> text_doc
    <mlclient.model.data.TextDocument object at 0x7f9200920e20>

    >>> bin_doc = next(doc for doc in docs if doc.uri == "/doc-4.zip")
    >>> bin_doc
    <mlclient.model.data.BinaryDocument object at 0x7f9200920970>

**Read documents from a custom database**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     doc = docs_client.read("/doc-1.xml", database="App-Services")

    >>> doc
    <mlclient.model.data.XMLDocument object at 0x7f92009b4700>


CREATE / UPDATE
"""""""""""""""

**Put a document**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.model import DocumentFactory

    >>> uri = "/doc-2.json"
    >>> content = {"root": {"child": "data"}}
    >>> doc = DocumentFactory.build_document(uri=uri, content=content)
    >>> doc
    <mlclient.model.data.JSONDocument object at 0x7f9200920f70>

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc)
    >>> resp
    {'documents': [{'uri': '/doc-2.json', 'mime-type': 'application/json', 'category': ['metadata', 'content']}]}


**Put a document with metadata**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.model import DocumentFactory, Metadata

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
    >>> from mlclient.model import DocumentFactory, DocumentType

    >>> uri = "/doc-1.xml"
    >>> content = b"<root><child>data</child></root>"
    >>> doc = DocumentFactory.build_raw_document(
    ...     uri=uri,
    ...     content=content,
    ...     doc_type=DocumentType.XML,
    ... )
    >>> doc
    <mlclient.model.data.RawDocument object at 0x7f9200929430>

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc)
    >>> resp
    {'documents': [{'uri': '/doc-1.xml', 'mime-type': 'application/xml', 'category': ['metadata', 'content']}]}


**Put a raw document with metadata**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.model import DocumentFactory, DocumentType

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
    >>> from mlclient.model import DocumentFactory

    >>> uri = "/doc-2.json"
    >>> content = {"root": {"child": "data"}}
    >>> doc = DocumentFactory.build_document(uri=uri, content=content)
    >>> doc
    <mlclient.model.data.JSONDocument object at 0x7f9200920f70>

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc, database="Documents")
    >>> resp
    {'documents': [{'uri': '/doc-2.json', 'mime-type': 'application/json', 'category': ['metadata', 'content']}]}

**Update document's metadata**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.model import Metadata, MetadataDocument

    >>> uri = "/doc-2.json"
    >>> metadata = Metadata(collections=["some-collection"])
    >>> doc = MetadataDocument(uri, metadata)
    >>> doc
    <mlclient.model.data.MetadataDocument object at 0x7f9200929e20>

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...     resp = docs_client.create(doc)
    >>> resp
    {'documents': [{'uri': '/doc-2.json', 'mime-type': '', 'category': ['metadata']}]}


**Put multiple documents**

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.model import DocumentFactory, DocumentType
    
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
    >>> from mlclient.model import DocumentFactory, DocumentType, Metadata
    
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

**Get all logs**

*8002_ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002)


.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.clients import LogType

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, log_type=LogType.ERROR)


*8002_AccessLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.clients import LogType

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, log_type=LogType.ACCESS)


*8002_RequestLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager
    >>> from mlclient.clients import LogType

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=8002, log_type=LogType.REQUEST)


*ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs()


*TaskServer_ErrorLog.txt*

.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server=0)


.. code-block:: python

    >>> from mlclient import MLManager

    >>> with MLManager("local").get_logs_client() as client:
    ...     logs = client.get_logs(app_server="TaskServer")
