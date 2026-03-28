[![License](https://img.shields.io/github/license/monasticus/mlclient?label=License&style=plastic)](https://github.com/monasticus/mlclient/blob/main/LICENSE)
[![Version](https://img.shields.io/pypi/v/mlclient?color=blue&label=PyPI&style=plastic)](https://pypi.org/project/mlclient/)
[![Python](https://img.shields.io/pypi/pyversions/mlclient?logo=python&label=Python&style=plastic)](https://www.python.org/)
[![Read the Docs](https://img.shields.io/readthedocs/mlclient/0.4.1?style=plastic&logo=readthedocs)](https://mlclient.readthedocs.io/en/0.4.1)  
[![Build](https://img.shields.io/github/actions/workflow/status/monasticus/mlclient/unit-test.yml?label=Test%20MLClient&style=plastic)](https://github.com/monasticus/mlclient/actions/workflows/unit-test.yml?query=branch%3Amain)
[![Code Coverage](https://img.shields.io/badge/Code%20Coverage-100%25-brightgreen?style=plastic)](https://github.com/monasticus/mlclient/actions/workflows/coverage-badge.yml?query=branch%3Amain)

# ML Client

Read the full documentation at [Read the Docs](https://mlclient.readthedocs.io).
___

ML Client is a python library providing a python API to manage a MarkLogic instance.

Low-level (raw HTTP):
```python
>>> from mlclient import MLClient
>>> config = {
...     "host": "localhost",
...     "port": 8002,
...     "username": "admin",
...     "password": "admin",
... }
>>> with MLClient(**config) as ml:
...     resp = ml.http.post(
...         "/v1/eval",
...         body={"xquery": "xdmp:database() => xdmp:database-name()"},
...     )
...     print(resp.text)
...
--6a5df7d535c71968
Content-Type: text/plain
X-Primitive: string

App-Services
--6a5df7d535c71968--
```

Mid-level (REST API groups):
```python
>>> from mlclient import MLClient
>>> config = {
...     "host": "localhost",
...     "port": 8002,
...     "username": "admin",
...     "password": "admin",
... }
>>> with MLClient(**config) as ml:
...     resp = ml.rest.eval.post(
...         xquery="xdmp:database() => xdmp:database-name()",
...     )
...     print(resp.text)
...
--6a5df7d535c71968
Content-Type: text/plain
X-Primitive: string

App-Services
--6a5df7d535c71968--
```

High-level (services):
```python
>>> from mlclient import MLClient
>>> config = {
...     "host": "localhost",
...     "port": 8002,
...     "username": "admin",
...     "password": "admin",
... }
>>> with MLClient(**config) as ml:
...     result = ml.eval.xquery(
...         "xdmp:database() => xdmp:database-name()",
...     )
...     print(result)
...
App-Services
```

## Installation

Install MLClient with pip

```sh
pip install mlclient
```
