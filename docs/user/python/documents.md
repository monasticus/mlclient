# Documents

`ml.documents` is the higher-level
[DocumentsService][mlclient.services.DocumentsService] for
`/v1/documents`. It exposes three operations - `read`, `write` (create or update)
and `delete` - that work with typed `Document` models instead of raw multipart
bodies.

Every operation accepts one URI or many, an optional `database`, and a `txid`
to run inside a [transaction](transactions.md). `read` and `write` also carry
metadata; `write` and `delete` also handle temporal collections.

Before the operations, two models are worth knowing: `Document` (what `read`
returns and `write` accepts) and `Metadata`.

## The `Document` model

### Types

A document is one of five typed subclasses, chosen by content:

| Subclass          | Content type                    | `content_string` | `content_bytes` |
|-------------------|---------------------------------|:----------------:|:---------------:|
| `XMLDocument`     | `ElementTree` / `str` / `bytes` | yes              | yes             |
| `JSONDocument`    | `dict` / `str` / `bytes`        | yes              | yes             |
| `TextDocument`    | `str` / `bytes`                 | yes              | yes             |
| `BinaryDocument`  | `bytes`                         | `None`           | yes             |
| `MetadataDocument`| none (metadata only)            | `None`           | `None`          |

### Building a document

`Document.create` infers the type from the content and the URI extension:

```python
>>> from mlclient.models import Document

>>> type(Document.create("/doc-1.xml", "<root><child>data</child></root>")).__name__
'XMLDocument'

>>> type(Document.create("/doc-2.json", {"root": {"child": "data"}})).__name__
'JSONDocument'
```

The typed factories `Document.xml`, `Document.json`, `Document.text` and
`Document.binary` force a type instead of inferring one - use them when the URI
extension would mislead the inference (`.log` text, `.dat` binary):

```python
>>> type(Document.text("/notes/2024-01.log", "line one\nline two")).__name__
'TextDocument'
```

`Document.metadata_update` builds a `MetadataDocument` for a metadata-only
change - see [Update only the metadata](#update-only-the-metadata).

### Inspecting a document

Whatever the subclass, the same accessors read it back. `content` is typed per
subclass (`dict` for JSON, `ElementTree` for XML); `content_string` and
`content_bytes` give the serialized forms:

```python
>>> doc = Document.create("/doc-2.json", {"root": {"child": "data"}})

>>> doc.uri
'/doc-2.json'

>>> doc.doc_type
<DocumentType.JSON: 'json'>

>>> doc.content
{'root': {'child': 'data'}}

>>> doc.content_string
'{"root": {"child": "data"}}'
```

## The `Metadata` model

`Metadata` holds the five categories MarkLogic keeps beside a document:
`collections`, `permissions`, `properties`, `quality` and `metadata_values`.

### Structured metadata

Build it field by field:

```python
>>> from mlclient.models import Metadata

>>> metadata = Metadata(collections=["some-collection"], quality=2)
>>> metadata.to_json()
{'collections': ['some-collection'], 'permissions': [], 'properties': {}, 'quality': 2, 'metadataValues': {}}
```

### Raw metadata

When you already hold a JSON or XML metadata payload, pass it as `raw` - the
format is auto-detected and parsing is deferred until a field is read:

```python
>>> metadata = Metadata(raw=b'{"collections": ["some-collection"]}')
>>> metadata.collections()
['some-collection']
```

`Document.create(..., metadata=...)` accepts a `Metadata`, or the raw `bytes` /
`str` payload directly - see [Write with raw metadata](#write-with-raw-metadata).

## Read

`read` returns a single `Document` for a string URI, or a `dict` keyed by URI
for a collection of URIs.

### Read a single document

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     doc = ml.documents.read("/doc-1.xml")

>>> doc.uri
'/doc-1.xml'

>>> doc.doc_type
<DocumentType.XML: 'xml'>

>>> doc.content_string
'<root><child>data</child></root>'
```

### Read multiple documents

A list, tuple or set of URIs returns a `dict` keyed by URI, each value typed
from its own content:

```python
>>> with MLClient() as ml:
...     docs = ml.documents.read(["/doc-1.xml", "/doc-2.json", "/doc-4.zip"])

>>> {uri: type(doc).__name__ for uri, doc in docs.items()}
{'/doc-1.xml': 'XMLDocument', '/doc-2.json': 'JSONDocument', '/doc-4.zip': 'BinaryDocument'}
```

### Read as string or bytes

`content_string` and `content_bytes` give the serialized forms of any
content-bearing document:

```python
>>> with MLClient() as ml:
...     doc = ml.documents.read("/doc-1.xml")

>>> doc.content_string
'<root><child>data</child></root>'

>>> doc.content_bytes
b'<root><child>data</child></root>'
```

### Read with metadata

Pass `category` to fetch metadata. The values are `Category` enum members (or
their string equivalents). `[Category.CONTENT, Category.METADATA]` returns the
content document with its `.metadata` populated:

```python
>>> from mlclient.models import Category

>>> with MLClient() as ml:
...     doc = ml.documents.read(
...         "/doc-1.xml",
...         category=[Category.CONTENT, Category.METADATA],
...     )

>>> doc.content_string
'<root><child>data</child></root>'

>>> doc.metadata.to_json()
{'collections': [], 'permissions': [], 'properties': {}, 'quality': 0, 'metadataValues': {}}
```

### Read metadata only

Dropping `Category.CONTENT` returns a `MetadataDocument` - no content body, just
the requested metadata categories:

```python
>>> with MLClient() as ml:
...     doc = ml.documents.read("/doc-1.xml", category=[Category.COLLECTIONS])

>>> doc
<mlclient.models.MetadataDocument object at 0x7f9200929e20>

>>> doc.content_string is None
True

>>> doc.metadata.collections()
['some-collection']
```

### Stream a large URI list

`read` materializes every document into a `dict`. `read_stream` yields each one
as it arrives and transparently splits a long URI list into several requests
(each staying under the httpx URL-length limit) - prefer it for large batches:

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client() as ml:
...     for doc in ml.documents.read_stream(["/doc-1.xml", "/doc-2.json"]):
...         print(doc.uri)
```

### Read from a custom database

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("my-app") as ml:
...     doc = ml.documents.read("/doc-1.xml", database="Documents")
```

## Write (create or update)

`write` accepts one `Document`, one `Metadata` (default metadata for a batch),
or a list mixing both.

### Write content

```python
>>> from mlclient.models import Document

>>> doc = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> with MLClient() as ml:
...     ml.documents.write(doc)
```

### Write content with metadata

Attach a `Metadata` to the document and both parts are written together:

```python
>>> from mlclient.models import Document, Metadata

>>> metadata = Metadata(collections=["some-collection"])
>>> doc = Document.create(
...     "/doc-2.json",
...     {"root": {"child": "data"}},
...     metadata=metadata,
... )
>>> with MLClient() as ml:
...     ml.documents.write(doc)
```

### Write with raw metadata

`metadata` also accepts a raw JSON/XML payload as `bytes` or `str`, skipping the
`Metadata` model entirely:

```python
>>> doc = Document.create(
...     "/doc-1.xml",
...     "<root><child>data</child></root>",
...     metadata=b'{"collections": ["some-collection"]}',
... )
>>> with MLClient() as ml:
...     ml.documents.write(doc)
```

### Update only the metadata

`Document.metadata_update` builds a `MetadataDocument` that rewrites a
document's metadata without touching its content body:

```python
>>> metadata = Metadata(collections=["some-collection"])
>>> doc = Document.metadata_update("/doc-2.json", metadata)
>>> with MLClient() as ml:
...     ml.documents.write(doc)
```

For a read-modify-write that preserves the other categories, see the
[collection update recipe](../../recipes.md#replace-a-collection-without-rewriting-content).

### Write multiple documents

```python
>>> doc_1 = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> doc_2 = Document.create("/doc-2.json", {"root": {"child": "data"}})
>>> with MLClient() as ml:
...     ml.documents.write([doc_1, doc_2])
```

### Write with default metadata for a batch

A bare `Metadata` in the list is default metadata: it applies to every document
after it that carries none of its own.

```python
>>> default_metadata = Metadata(collections=["some-collection"])
>>> doc_1 = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> doc_2 = Document.create("/doc-2.json", {"root": {"child": "data"}})
>>> with MLClient() as ml:
...     ml.documents.write([default_metadata, doc_1, doc_2])
```

### Write to a custom database

```python
>>> doc = Document.create("/doc-2.json", {"root": {"child": "data"}})
>>> with MLClient() as ml:
...     ml.documents.write(doc, database="Documents")
```

## Delete

### Delete one or many documents

A string deletes one document; a list, tuple or set deletes many, split across
requests the same way `read` batches its URIs.

```python
>>> with MLClient() as ml:
...     ml.documents.delete("/doc-1.xml")

>>> with MLClient() as ml:
...     ml.documents.delete(["/doc-1.xml", "/doc-2.json", "/doc-4.zip"])
```

### Delete metadata categories

With `category`, the document stays but the listed metadata categories are
removed or reset to their defaults:

```python
>>> from mlclient.models import Category

>>> with MLClient() as ml:
...     ml.documents.delete(
...         "/doc-1.xml",
...         category=[Category.PROPERTIES, Category.COLLECTIONS],
...     )
```

### Delete from a custom database

```python
>>> with MLClient() as ml:
...     ml.documents.delete("/doc-1.xml", database="Documents")
```

## Temporal documents

`write` and `delete` take `temporal_collection` to operate on a
[bitemporal](https://docs.marklogic.com/guide/temporal) document.

### Write into a temporal collection

```python
>>> doc = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> with MLClient() as ml:
...     ml.documents.write(doc, temporal_collection="temporal-collection")
```

### Delete (close) a temporal document

Deleting within a temporal collection closes the current version - earlier
versions remain queryable:

```python
>>> with MLClient() as ml:
...     ml.documents.delete("/doc-1.xml", temporal_collection="temporal-collection")
```

### Wipe every version

`wipe_temporal=True` removes all versions instead of closing the latest:

```python
>>> with MLClient() as ml:
...     ml.documents.delete(
...         "/doc-1.xml",
...         temporal_collection="temporal-collection",
...         wipe_temporal=True,
...     )
```

## Within a transaction

`read`, `write` and `delete` accept a `txid` to run inside an open
multi-statement transaction. Pass the id explicitly, or spread a
`TransactionService` with `**` to carry both the `txid` and its database. See
[Transactions](transactions.md) for the full lifecycle.

```python
>>> doc = Document.create("/doc-1.xml", "<root><child>data</child></root>")
>>> with MLClient() as ml:
...     with ml.transaction() as txn:
...         ml.documents.write(doc, **txn)
...         ml.documents.read("/doc-1.xml", txid=txn.id)
```
