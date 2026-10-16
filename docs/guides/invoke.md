# Invoke modules

`ml.invoke` is the [InvokeService][mlclient.services.InvokeService]: it runs an
XQuery or JavaScript module already installed in MarkLogic and returns the
result parsed into Python, the same way [`ml.eval`](eval.md) does for code sent
from the client.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result = ml.invoke.module("/ext/words.xqy", word1="hello", word2="world")
>>> result
['hello', 'world', 'hello world']
```

The module path resolves against the modules database or directory of the App
Server receiving the request, so select the [connection](clients.md) whose App
Server has the module installed. Its suffix selects the language: `.sjs` runs as
JavaScript, `.xqy` as XQuery. Invoking requires the `xdmp-invoke` privilege, not
`xdmp-eval`.

`module()` accepts a `database`, a `txid` to run inside a
[transaction](transactions.md), and `output_type` to skip parsing.

## Pass variables

Pass external variables as a dict, as keyword arguments, or both. A keyword
argument overrides a dict entry of the same name:

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result = ml.invoke.module(
...         "/ext/words.sjs",
...         variables={"word1": "hello"},
...         word2="world",
...     )
>>> result
['hello', 'world', 'hello world']
```

Name a namespaced XQuery variable in Clark notation (`{namespace-uri}local-name`),
as described in [Evaluate code](eval.md#within-a-namespace).

## Get raw output

Pass `str` or `bytes` as `output_type` to receive each item verbatim:

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     result = ml.invoke.module("/ext/report.xqy", output_type=str)
```

## Reuse database and transaction settings

Call the service to create a scoped copy without sending a request:

```python
with MLClient() as ml:
    catalog = ml.invoke(database="catalog")
    report = catalog.module("/ext/report.xqy")
```

The scope works as in [`ml.eval`](eval.md#reuse-database-and-transaction-settings):
per-operation `database=` and `txid=` override it, and `None` clears a value.

## Within a transaction

Spread a [`TransactionService`][mlclient.services.TransactionService] with `**`
to run the module inside it:

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     with ml.transaction() as txn:
...         ml.invoke.module("/ext/insert.xqy", uri="/doc-1.xml", **txn)
```

See [InvokeService.module][mlclient.services.InvokeService.module] for the full
signature, and the [`ml invoke`](../cli/invoke.md) command for the CLI.
