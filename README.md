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

By default MLClient connects to `localhost:8000` over HTTP with digest auth (`admin`/`admin`).
Pass `host`, `port`, `username`, `password`, or `auth` to override:

```python
config = {
    "host": "ml.example.com",
    "port": 8040,
    "username": "my-user",
    "password": "my-password",
    "auth": "digest",
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

    xml_doc = Document.create("/patient/record-2.xml", "<patient><name>Jones</name></patient>")
    ml.documents.write(xml_doc)

    json_doc = Document.create("/patient/record-3.json", {"name": "Brown", "id": "003"})
    ml.documents.write(json_doc)
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

## Connection & authentication

Connection (transport) and authentication (identity) are configured separately.
The transport is chosen from `protocol`, `ssl`, and `cloud`; the auth method from
`auth`. Invalid combinations are rejected when the client is created, not at
request time.

Supported connection modes:

| Mode             | How to select it                              | Protocol / port |
|------------------|-----------------------------------------------|-----------------|
| HTTP             | default                                       | `http` / `8000` |
| HTTPS            | `protocol="https"`                            | `https`         |
| Mutual TLS       | `ssl=SSLConfig(cert_file=..., key_file=...)`  | `https`         |
| MarkLogic Cloud  | `cloud=CloudConfig(api_key=..., base_path=...)` | `https` / `443` |

Supported authentication methods (`auth=`):

| `auth` value                          | Method               | Credentials from |
|---------------------------------------|----------------------|------------------|
| `"digest"` (default)                  | HTTP digest          | `username` / `password` |
| `"basic"`                             | HTTP basic           | `username` / `password` |
| `"certificate"`                       | Client certificate   | `ssl` client cert (auto-selected with mutual TLS) |
| `"kerberos"`                          | Kerberos / SPNEGO    | ambient ticket cache (`mlclient[kerberos]`) |
| `AuthConfig(method="oauth", ...)`     | OAuth 2.0 Bearer     | pre-acquired token |
| `AuthConfig(method="kerberos", ...)`  | Kerberos / SPNEGO    | as above, with a custom SPN (`service` / `hostname`) |
| `None`                                | application-level    | none (Cloud handles its own) |
| any `httpx.Auth`                      | custom               | your handler |

See the [Connection & authentication guide](https://mlclient.readthedocs.io)
for initialization examples per method and the full matrix of valid and rejected
combinations.

## CLI

```sh
ml call eval -e local -x "xdmp:database() => xdmp:database-name()"
ml call logs -e local -a 8002 --regex "XDMP-.*"
```

---

Full documentation at [Read the Docs](https://mlclient.readthedocs.io).
