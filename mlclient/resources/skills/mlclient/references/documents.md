# Documents, metadata and transactions

Prefer DocumentsService over manually parsing multipart responses. Import
`Document`, `Metadata`, `Category` from `mlclient.models` and local I/O helpers
from `mlclient.io`. The async service has the same request parameters.

```python
from mlclient import MLClientManager
from mlclient.models import Document, Metadata

with MLClientManager('dev').get_client('content') as ml:
    one = ml.documents.read('/products/one.json', category=['content', 'metadata'])
    many = ml.documents.read(['/products/one.json', '/products/two.json'])
    print(one.uri, one.doc_type, one.content, one.metadata)
    # Explicit replacement: supply the intended metadata alongside content.
    replacement = Document.json(
        '/products/one.json', {'name': 'Coffee'},
        metadata=Metadata(collections=['products']),
    )
    ml.documents.write(replacement)
```

A string URI returns one Document; an iterable returns a URI-keyed dict.
`.content` parses by document type; `.content_bytes` preserves bytes;
`.content_string` is for textual display. XML parsing uses ElementTree,
JSON yields Python values, binary stays bytes. Bulk reads/writes reduce round trips.
Use `category` deliberately: metadata-only results have no content.

Use `Document.xml/json/text/binary` for explicit types; `Document.create` infers
where possible. Use `Document.metadata_update(uri, metadata)` for a metadata-only
write. `Metadata` contains collections, permissions, properties, quality and
metadata-values. Treat category replacement as replacement; fetch current
metadata and retain the pieces that must survive. Do not accidentally remove
reader/updater permissions when replacing metadata.

`ml.documents.write` creates or replaces content/metadata; it is not a merge patch.
Use `ml.http.request("PATCH", "/v1/documents", params={"uri": uri}, body=...)`
for a REST PATCH; the current named documents API has get/post/delete only. Read the
versioned PATCH contract for XML/JSON patch format, path namespaces, cardinality
and headers. Use raw HTTP when wrapper parameters do not expose needed headers,
including ETag/If-Match optimistic concurrency. A read-modify-write without a
transaction or concurrency guard can overwrite another writer.

## Export and import

```python
from mlclient.io import DocumentsWriter, DocumentsLoader

# Inside an async client context:
docs = await ml.documents.read(uris, category=['content', 'metadata'])
await DocumentsWriter.write(docs.values(), './export')

# DocumentsLoader is a local synchronous iterator; write bounded batches.
loaded = DocumentsLoader.load('./export', uri_prefix='/archive')
```

Writer preserves binary and emits metadata sidecars, Loader recognizes
`.metadata.json` / `.metadata.xml`. Check the URI mapping with a small batch
before importing. Writer maps URIs to filesystem paths; validate that all mapped
paths remain under the intended output directory, especially for untrusted URIs
with `..`. The [export template](../assets/export_documents.py) does this check.
Sidecar names replace the content extension: `/a.bin` gets `a.metadata.json`.
Documents sharing a stem (such as `/a.json` and `/a.xml`) can collide in metadata
sidecars. Different URIs can also collide on case-insensitive filesystems; preflight mappings
before a cross-platform export. Local export is not a database backup.

`read_stream` yields models from a buffered HTTP response; it is not an
unbounded HTTP streaming guarantee. Chunk URI lists and flush each batch to disk
for large exports. Select a narrow URI query; do not retrieve all documents just
to filter locally. Bulk import must cap bytes as well as count for large documents.

## Transactions

```python
async with await ml.transaction(database='Documents', time_limit=60) as txn:
    await ml.documents.write([first_document, second_document], **txn)
    result = await ml.documents.read(first_document.uri, **txn)
```

The sync form is `with ml.transaction(...) as txn:`. Context managers commit on
success and roll back on exceptions. Pass `**txn` to each operation to bind txid
and its database. Keep dependent transaction work sequential; do not spread one
transaction across concurrent jobs or leave it open while waiting for human input.
An HTTP timeout does not cancel or roll back server work by itself. Investigate
uncertain mutation outcomes before replaying requests.

Docs: [documents](https://monasticus.github.io/mlclient/user/python/documents/),
[transactions](https://monasticus.github.io/mlclient/user/python/transactions/).
