# API layers and raw HTTP

Below the high-level services, MLClient exposes three mid-level API clients that correspond to MarkLogic's API tiers. They work with [ApiCall][mlclient.calls.ApiCall] objects, which are python representations of MarkLogic endpoint calls. You can use these clients to send customized requests that are not supported by the high-level service API, or to handle the responses yourself.

## RestApi

[RestApi][mlclient.api.RestApi] provides access to `/v1/*` endpoints on the main port.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.rest.eval.post(
...         xquery="xdmp:database() => xdmp:database-name()",
...     )
...     parsed = ml.parser.parse(resp)
...     print(parsed)
...
App-Services
```

### Transactions

`ml.rest.transactions` has no context manager: create the transaction, thread its id through each call, and drive commit or rollback yourself. The id is the last path segment of the `Location` header on the `303` create response:

```python
>>> from mlclient import MLClient
>>> from mlclient.models import Document

>>> doc = Document.create("/doc-1.xml", "<root>data</root>")
>>> with MLClient() as ml:
...     location = ml.rest.transactions.create().headers["Location"]
...     txid = location.rsplit("/", 1)[-1]
...     try:
...         ml.documents.write(doc, txid=txid)
...         ml.rest.transactions.post(txid, result="commit")
...     except Exception:
...         ml.rest.transactions.post(txid, result="rollback")
...         raise
```

## ManageApi

[ManageApi][mlclient.api.ManageApi] provides access to `/manage/v2/*` endpoints on port 8002.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.manage.databases.get_properties(
...         "Documents", data_format="json",
...     )
...     print(resp.json()["database-name"])
...
Documents
```

## AdminApi

[AdminApi][mlclient.api.AdminApi] provides access to `/admin/v1/*` endpoints on port 8001.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.admin.get_timestamp()
...     print(resp.text)
...
2024-06-21T14:08:32.130813Z
```

# Low-level HTTP

The low-level [HttpClient][mlclient.HttpClient] lets you send raw HTTP requests. It is accessible via `ml.http`.

## GET request

*A simple GET request*

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.http.get("/manage/v2/servers")
```

*Custom parameters and headers*

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.http.get(
...         "/manage/v2/servers",
...         params={"format": "json"},
...         headers={"custom-header": "custom-value"},
...     )
```

## POST request

*A simple POST request*

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.http.post(
...         "/manage/v2/databases",
...         {"database-name": "CustomDatabase"},
...     )
```

*Custom parameters and headers*

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.http.post(
...         "/v1/eval",
...         {"xquery": "fn:current-dateTime()"},
...         params={"database": "Documents"},
...         headers={"Content-Type": "application/x-www-form-urlencoded"},
...     )
```

## PUT request

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.http.put(
...         "/manage/v2/databases/CustomDatabase/properties",
...         {"enabled": False},
...         headers={"Content-Type": "application/json"}
...     )
```

## DELETE request

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.http.delete(
...         "/manage/v2/databases/CustomDatabase",
...         params={"forest-delete": "configuration"}
...     )
```

## Raw HTTP request bodies

For `ml.http.request` and its convenience methods (also on the asynchronous client), strings and bytes are sent as raw content even with a JSON content type. Dictionaries are JSON-encoded when the content type is JSON; otherwise they are submitted as form data. Header names are case-insensitive.
