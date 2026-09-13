# Documents

## Document models

`Document` represents a URI, content and optional metadata. Use `Document.json`,
`Document.xml`, `Document.text` or `Document.binary` factories for content, and
`Document.metadata_update` for metadata-only changes. `Metadata` holds collections,
permissions, properties, quality and metadata values. Reading returns the
appropriate document model; reading multiple URIs returns a dictionary by URI.

For a complete metadata-only operation, see the
[collection update recipe](../../recipes.md#replace-a-collection-without-rewriting-content).

## Read

**Read a document**

```python
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
```

**Read a document as string or bytes**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     doc = ml.documents.read("/doc-1.xml")

>>> doc.doc_type
<DocumentType.XML: 'xml'>

>>> doc.content_string
'''<?xml version="1.0" encoding="UTF-8"?>
<SomeEntity>
    <ChildNode1>00001</ChildNode1>
    <ChildNode2>888e2050-7148-42c4-b33a-b3dd3505b87b</ChildNode2>
</SomeEntity>'''

>>> doc.content_bytes
b'''<?xml version="1.0" encoding="UTF-8"?>
<SomeEntity>
    <ChildNode1>00001</ChildNode1>
    <ChildNode2>888e2050-7148-42c4-b33a-b3dd3505b87b</ChildNode2>
</SomeEntity>'''
```

**Read a document with metadata**

```python
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
```

**Read multiple documents**

```python
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
```

**Stream documents one at a time**

`read_stream` yields each document as it arrives instead of building the whole result in memory - preferable for large URI lists:

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     for doc in ml.documents.read_stream(["/doc-1.xml", "/doc-2.json"]):
...         print(doc.uri)
```

**Read documents from a custom database**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     doc = ml.documents.read("/doc-1.xml", database="App-Services")
```

## Write (create or update)

**Put a document**

```python
>>> from mlclient import MLClientManager
>>> from mlclient.models import Document

>>> doc = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.write(doc)
```

**Put a document with metadata**

```python
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
```

**Put a document with raw bytes metadata**

```python
>>> from mlclient import MLClientManager
>>> from mlclient.models import Document

>>> doc = Document.create(
...     "/doc-1.xml",
...     "<root><child>data</child></root>",
...     metadata=b'{"collections": ["some-collection"]}',
... )

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.write(doc)
```

**Put a document to a custom database**

```python
>>> from mlclient import MLClientManager
>>> from mlclient.models import Document

>>> doc = Document.create("/doc-2.json", {"root": {"child": "data"}})
>>> doc
<mlclient.models.documents.JSONDocument object at 0x7f9200920f70>

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.write(doc, database="Documents")
```

**Update document's metadata**

```python
>>> from mlclient import MLClientManager
>>> from mlclient.models import Document, Metadata

>>> metadata = Metadata(collections=["some-collection"])
>>> doc = Document.metadata_update("/doc-2.json", metadata)
>>> doc
<mlclient.models.documents.MetadataDocument object at 0x7f9200929e20>

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.write(doc)
```

**Put multiple documents**

```python
>>> from mlclient import MLClientManager
>>> from mlclient.models import Document

>>> doc_1 = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> doc_2 = Document.create("/doc-2.json", {"root": {"child": "data"}})

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.write([doc_1, doc_2])
```

**Put documents with default metadata**

```python
>>> from mlclient import MLClientManager
>>> from mlclient.models import Document, Metadata

>>> default_metadata = Metadata(collections=["some-collection"])
>>> doc_1 = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> doc_2 = Document.create("/doc-2.json", {"root": {"child": "data"}})

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.write([default_metadata, doc_1, doc_2])
```

## Delete

**Delete a document**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.delete("/doc-1.xml")
```

**Delete multiple documents**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.delete(
...         ["/doc-1.xml", "/doc-2.json", "/doc-3.xqy", "/doc-4.zip"]
...     )
```

**Delete a document from a custom database**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.delete("/doc-1.xml", database="Documents")
```

**Delete document's metadata**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.delete("/doc-1.xml", category=["properties", "collections"])
```

**Delete a temporal document**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.delete("/doc-1.xml", temporal_collection="temporal-collection")
```

**Wipe a temporal document**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     ml.documents.delete(
...        "/doc-1.xml",
...        temporal_collection="temporal-collection",
...        wipe_temporal=True,
... )
```

## Within a transaction

`read`, `write` and `delete` accept a `txid` to run inside an open multi-statement transaction. Pass the id explicitly, or spread a `TransactionService` with `**` to carry both the `txid` and the transaction's database. See [TransactionService](transactions.md) for the full transaction lifecycle.

```python
>>> from mlclient import MLClientManager
>>> from mlclient.models import Document

>>> doc = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     with ml.transaction() as txn:
...         ml.documents.write(doc, **txn)
...         ml.documents.read("/doc-1.xml", txid=txn.id)
```
