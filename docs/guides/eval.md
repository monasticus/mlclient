# Evaluate code

`ml.eval` is the [EvalService][mlclient.services.EvalService]: it evaluates
XQuery or JavaScript on the server and returns the result already parsed into
Python - a `fn:current-dateTime()` comes back as a `datetime.datetime`, a JSON
node as a `dict`, and so on.

The methods:

| Method            | Evaluates                                  |
|-------------------|--------------------------------------------|
| `xquery` (`xqy`)  | a raw XQuery string                        |
| `javascript` (`js`) | a raw JavaScript string                   |
| `file`            | a file, language detected from its suffix  |
| `execute`         | general-purpose dispatch over `xq`/`js`/`file` |
| `expression`      | an expression built with the XQuery API     |

These methods accept a `database`, a `txid` to run inside a
[transaction](transactions.md), and `output_type` to skip parsing. Raw code
methods also accept `variables`; expressions bind their arguments automatically.

## Evaluate a string

### XQuery

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result = ml.eval.xquery("fn:current-dateTime()")
>>> result
datetime.datetime(2024, 2, 22, 11, 38, 32, 709484, tzinfo=datetime.timezone.utc)
```

### JavaScript

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result = ml.eval.javascript("fn.currentDateTime()")
>>> result
datetime.datetime(2024, 2, 22, 11, 39, 22, 264102, tzinfo=datetime.timezone.utc)
```

## Evaluate a file

`file` detects the language from the suffix:

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result1 = ml.eval.file("./xqy-code-to-eval.xqy")
...     result2 = ml.eval.file("./js-code-to-eval.js")
```

The recognized suffixes are:

| Language   | Suffixes                                     |
|------------|----------------------------------------------|
| XQuery     | `.xq`, `.xql`, `.xqm`, `.xqu`, `.xquery`, `.xqy` |
| JavaScript | `.js`, `.sjs`                                |

Any other suffix raises [`UnsupportedFileExtensionError`][mlclient.exceptions.UnsupportedFileExtensionError].

## Pass variables

### As a dict

```python
>>> from mlclient import MLClient

>>> xq = '''
... declare variable $DAYS external;
...
... fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'''

>>> with MLClient() as ml:
...     result = ml.eval.xquery(xq, variables={"DAYS": 5})
>>> result
datetime.datetime(2024, 2, 17, 12, 17, 49, 556376, tzinfo=datetime.timezone.utc)
```

### As keyword arguments

The same variables can be passed as keyword arguments:

```python
>>> from mlclient import MLClient

>>> xq = '''
... declare variable $DAYS external;
...
... fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'''

>>> with MLClient() as ml:
...     result = ml.eval.xquery(xq, DAYS=5)
>>> result
datetime.datetime(2024, 2, 17, 12, 19, 45, 225135, tzinfo=datetime.timezone.utc)
```

### Within a namespace

Name a namespaced variable in Clark notation (`{namespace-uri}local-name`):

```python
>>> from mlclient import MLClient
>>> from mlclient.xquery import LOCAL_NS_URI

>>> xq = '''
... declare variable $local:DAYS external;
...
... fn:current-dateTime() - xs:dayTimeDuration("P" || $local:DAYS || "D")'''

>>> with MLClient() as ml:
...     result = ml.eval.xquery(
...         xq,
...         variables={
...             f"{{{LOCAL_NS_URI}}}DAYS": 5,
...         },
...     )
>>> result
datetime.datetime(2024, 2, 17, 12, 21, 28, 547853, tzinfo=datetime.timezone.utc)
```

## Get raw output

Without `output_type` the result is parsed into a Python object. Pass `str` or
`bytes` to receive the server's response verbatim instead:

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result = ml.eval.xquery("fn:current-dateTime()", output_type=str)
>>> result
'2024-02-22T12:24:40.362014Z'
```

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result = ml.eval.xquery("fn:current-dateTime()", output_type=bytes)
>>> result
b'2024-02-22T12:24:53.677793Z'
```

## Evaluate on a custom database

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result = ml.eval.xquery(
...         "xdmp:database() => xdmp:database-name()",
...         database="Documents",
...     )
>>> result
'Documents'
```

## Evaluate an XQuery expression

`expression()` evaluates a builder expression and parses its result:

```python
from mlclient.xquery import fn

with MLClient() as ml:
    length = ml.eval.expression(fn.string_length("coffee"))
    print(length)  # 6
```

See the [XQuery API guide](../advanced/xquery-api.md) for composing expressions and calling
custom modules, and [EvalService.expression][mlclient.services.EvalService.expression]
for the full signature.

## Reuse database and transaction settings

Call the service to create a scoped copy without sending a request:

```python
with MLClient() as ml:
    catalog = ml.eval(database="catalog")
    count = catalog.xquery("fn:count(fn:collection())")
    default_database = catalog(database=None)
```

The shared [ServiceScope][mlclient.services.ServiceScope] holds `database` and
`txid`. The original service is unchanged. Per-operation `database=` and `txid=`
arguments override the scope; omitting them inherits it, and `None` clears a value.
Use `ml.eval(**txn)` for a series of operations inside a transaction. Async
services support the same scoping syntax.

## Within a transaction

Pass a `txid` to run inside an open multi-statement transaction, or spread a
[`TransactionService`][mlclient.services.TransactionService] with `**` to carry both the `txid` and its database. See
[Transactions](transactions.md) for the full lifecycle.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     with ml.transaction() as txn:
...         ml.eval.xquery('xdmp:document-insert("/doc-1.xml", <root/>)', **txn)
...         count = ml.eval.xquery("fn:count(fn:collection())", txid=txn.id)
```
