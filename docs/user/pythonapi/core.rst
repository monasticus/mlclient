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
    ...    doc = docs_client.read("/doc-1.xml", output_type=str)

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
    ...    doc = docs_client.read("/doc-1.xml", output_type=bytes)

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
    ...    doc = docs_client.read("/doc-1.xml", category=["content", "metadata"])

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
    ...   "/some/dir/doc1.xml",
    ...   "/some/dir/doc2.json",
    ...   "/some/dir/doc3.xqy",
    ...   "/some/dir/doc4.zip",
    ... ]
    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...    docs = docs_client.read(uris)

    >>> len(docs)
    4

    >>> xml_doc = next(doc for doc in docs if doc.uri == "/some/dir/doc1.xml")
    >>> xml_doc
    <mlclient.model.data.XMLDocument object at 0x7f9200920a00>

    >>> json_doc = next(doc for doc in docs if doc.uri == "/some/dir/doc2.json")
    >>> json_doc
    <mlclient.model.data.JSONDocument object at 0x7f9200920430>

    >>> text_doc = next(doc for doc in docs if doc.uri == "/some/dir/doc3.xqy")
    >>> text_doc
    <mlclient.model.data.TextDocument object at 0x7f9200920e20>

    >>> bin_doc = next(doc for doc in docs if doc.uri == "/some/dir/doc4.zip")
    >>> bin_doc
    <mlclient.model.data.BinaryDocument object at 0x7f9200920970>

**Read documents from a custom database**

.. code-block:: python

    >>> from mlclient import MLManager

    >>> manager = MLManager("local")
    >>> with manager.get_documents_client("app-services") as docs_client:
    ...    doc = docs_client.read("/doc-1.xml", database="App-Services")

    >>> doc
    <mlclient.model.data.XMLDocument object at 0x7f92009b4700>


EvalClient
^^^^^^^^^^

LogsClient
^^^^^^^^^^
