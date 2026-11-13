# REST extensions

`ml.resources` is the [ResourcesService][mlclient.services.ResourcesService]: it
calls a resource service extension (a REST extension) installed in the REST API
instance of the connection, at `/v1/resources/{name}`, and returns the result
parsed into Python, the same way [`ml.eval`](eval.md) does.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     report = ml.resources.get("sales-report", {"year": 2026})
>>> report
{'year': '2026', 'total': 1250}
```

The service has one operation per HTTP method an extension can implement:
`get`, `post`, `put` and `delete`. Each runs the extension function of that
method, so calling a method the extension does not implement fails. The
extension must already be installed; mlclient only calls it. Select the
[connection](clients.md) whose REST App Server has it installed.

The result is parsed by its content type: JSON becomes a `dict` or `list`, XML an
element tree, text a `str`. An extension returning several documents answers
with `multipart/mixed`, which becomes a list with one item per document; no
content becomes `[]`.

Calling requires the `rest-reader` privilege, and `rest-writer` for `post`,
`put` and `delete`.

## Pass parameters

Pass the extension's parameters as a dict, by the names the extension reads.
MarkLogic expects them with the `rs:` prefix, which mlclient adds; a name that
already starts with `rs:`, for example copied from a URL, is sent unchanged.

| Python value | Sent as | The extension receives |
| --- | --- | --- |
| `{"year": 2026}` | `rs:year=2026` | `"2026"` |
| `{"draft": True}` | `rs:draft=true` | `"true"` |
| `{"tag": ["a", "b"]}` | `rs:tag=a&rs:tag=b` | the sequence `("a", "b")` |
| `{"rs:year": 2026}` | `rs:year=2026` | `"2026"` |
| `{"year": None}` | nothing | no value |

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     ml.resources.get("sales-report", {"year": 2026, "region": ["EU", "US"]})
```

## Send a body

`post` and `put` take a body as their second argument, and parameters as their
third:

| Body | Sent as |
| --- | --- |
| `dict` or `list` | JSON (`application/json`, or the given `content_type`) |
| `str` or `bytes` | as is, with the required `content_type` |
| a [`Document`][mlclient.models.Document] | its content, with the content type of its URI extension, or of its document type when the URI is missing |
| a list of `Document`s | `multipart/mixed`, one part per document |
| `None` (default) | no body; the extension still runs |

```python
>>> from mlclient import MLClient
>>> from mlclient.models import JSONDocument, XMLDocument

>>> with MLClient() as ml:
...     ml.resources.post("orders", {"sku": "A-1", "quantity": 2}, {"notify": True})
...     ml.resources.put("catalog", "<item id='A-1'/>", content_type="application/xml")
...     ml.resources.post(
...         "import",
...         [JSONDocument({"sku": "A-1"}), XMLDocument("<item id='A-2'/>")],
...     )
```

The extension receives each part of a multipart body as one input document.

## Reuse database and transaction settings

Call the service to create a scoped copy without sending a request:

```python
with MLClient() as ml:
    catalog = ml.resources(database="catalog")
    report = catalog.get("sales-report", {"year": 2026})
```

The scope works as in [`ml.eval`](eval.md#reuse-database-and-transaction-settings):
per-operation `database=` and `txid=` override it, and `None` clears a value.
Spread a [`TransactionService`][mlclient.services.TransactionService] with `**`
to run the extension inside a [transaction](transactions.md):

```python
with MLClient() as ml:
    with ml.transaction() as txn:
        ml.resources.post("orders", {"sku": "A-1"}, **txn)
```

## Errors

A failure MarkLogic describes raises
[`MarkLogicError`][mlclient.exceptions.MarkLogicError] with its message, for
example for an extension that is not installed (`RESTAPI-INVALIDREQ`) or a
method it does not implement. Invalid input that mlclient can see before
sending, such as a `str` body without `content_type`, raises
[`WrongParametersError`][mlclient.exceptions.WrongParametersError] and sends
no request.

## Who the extension runs as

The user an extension runs as depends on the MarkLogic version. MarkLogic
12.0.2 runs extensions as the internal `rest-transform-user`, which lacks
privileges such as `rest-reader` and `unprotected-uri`; MarkLogic 12.0.1 and
12.1.0 run them as the authenticated caller. An extension that reads protected
documents may therefore work on one version and fail on another with the same
credentials. Call `xdmp:get-current-user()` from inside the extension to check.

## Raw responses

[`ml.rest.resources`][mlclient.api.ResourcesApi] sends the same requests and
returns the raw [`httpx.Response`](https://www.python-httpx.org/api/#response),
with an `accept` header option for extensions that answer in several formats.
It adds the `rs:` prefix in the same way and accepts `dict`, `list`, `str` and
`bytes` bodies:

```python
with MLClient() as ml:
    response = ml.rest.resources.get(
        "sales-report",
        params={"year": 2026},
        accept="application/xml",
    )
```

See [ResourcesService][mlclient.services.ResourcesService] for the full
signatures.
