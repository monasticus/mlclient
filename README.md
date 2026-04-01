[![License](https://img.shields.io/github/license/monasticus/mlclient?label=License&style=plastic)](https://github.com/monasticus/mlclient/blob/main/LICENSE)
[![Version](https://img.shields.io/pypi/v/mlclient?color=blue&label=PyPI&style=plastic)](https://pypi.org/project/mlclient/)
[![Python](https://img.shields.io/pypi/pyversions/mlclient?logo=python&label=Python&style=plastic)](https://www.python.org/)
[![Read the Docs](https://img.shields.io/readthedocs/mlclient/0.4.1?style=plastic&logo=readthedocs)](https://mlclient.readthedocs.io/en/0.4.1)
[![Build](https://img.shields.io/github/actions/workflow/status/monasticus/mlclient/unit-test.yml?label=Test%20MLClient&style=plastic)](https://github.com/monasticus/mlclient/actions/workflows/unit-test.yml?query=branch%3Amain)
[![Code Coverage](https://img.shields.io/badge/Code%20Coverage-100%25-brightgreen?style=plastic)](https://github.com/monasticus/mlclient/actions/workflows/coverage-badge.yml?query=branch%3Amain)

# ML Client

A Python client for MarkLogic Server. Three API layers, async out of the box, CLI included.

Read the full documentation at [Read the Docs](https://mlclient.readthedocs.io).

## Installation

```sh
pip install mlclient
```

By default MLClient connects to `localhost:8000` with basic auth (`admin`/`admin`).
Pass `host`, `port`, `username`, `password`, or `auth_method` to override:

```python
config = {
    "host": "ml.example.com",
    "port": 8040,
    "username": "my-user",
    "password": "my-password",
    "auth_method": "digest",
}
ml = MLClient(**config)
```

## Quickstart

Evaluate XQuery and get a parsed Python object back - not raw multipart HTTP, not strings:

```python
from mlclient import MLClient

with MLClient() as ml:
    db_name = ml.eval.xquery("xdmp:database() => xdmp:database-name()")
    print(db_name)          # "Documents"
    print(type(db_name))    # <class 'str'>

    timestamp = ml.eval.xquery("fn:current-dateTime()")
    print(timestamp)        # 2024-06-21 14:08:32.130813+00:00
    print(type(timestamp))  # <class 'datetime.datetime'>
```

Read and write documents:

```python
from mlclient import MLClient
from mlclient.models import Document

with MLClient() as ml:
    doc = ml.documents.read("/patient/record-1.json")
    print(doc.uri)       # /patient/record-1.json
    print(doc.content)   # {"name": "Smith", "id": "001"}

    new_doc = Document.create("/patient/record-2.json", {"name": "Jones", "id": "002"})
    ml.documents.write(new_doc)
```

## More Control

Need the raw `httpx.Response`? Drop down to the mid-level API and use the built-in response parser when you want parsed results:

```python
with MLClient() as ml:
    resp = ml.rest.eval.post(xquery="xdmp:database() => xdmp:database-name()")
    print(resp.status_code)         # 200
    parsed = ml.parser.parse(resp)  # "Documents"
```

Three mid-level API clients cover all of MarkLogic's API tiers:

- `ml.rest` - REST Client API (`/v1/*`)
- `ml.manage` - Management API (`/manage/v2/*`, port 8002)
- `ml.admin` - Admin API (`/admin/v1/*`, port 8001)

Port routing is automatic. Manage and Admin requests go to ports 8002 and 8001 regardless of the main client port.

## Full Control

Send any HTTP request directly:

```python
with MLClient() as ml:
    resp = ml.http.post(
        "/v1/eval",
        body={"xquery": "xdmp:database() => xdmp:database-name()"},
    )
    print(resp.text)  # raw multipart/mixed response
```

## Async

`AsyncMLClient` mirrors `MLClient` 1:1 - every method is a coroutine:

```python
from mlclient import AsyncMLClient

async with AsyncMLClient() as ml:
    db_name = await ml.eval.xquery("xdmp:database() => xdmp:database-name()")
    doc = await ml.documents.read("/patient/record-1.xml")
    resp = await ml.http.get("/manage/v2/servers")
```

## CLI

```sh
ml call eval -e local -x "xdmp:database() => xdmp:database-name()"
ml call logs -e local -a 8002 --regex "XDMP-.*"
```

---

Full documentation at [Read the Docs](https://mlclient.readthedocs.io).
