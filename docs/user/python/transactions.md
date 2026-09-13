# Transactions

A multi-statement transaction groups several document or eval operations so they commit or roll back as a unit. Open one with `ml.transaction()`; the returned `TransactionService` is a context manager that commits on a clean exit and rolls back if the block raises.

Spread it with `**` into any content operation to run that operation inside the transaction - it unpacks to `txid` (and `database`, when the transaction was opened against one).

## Commit on clean exit

```python
>>> from mlclient import MLClientManager
>>> from mlclient.models import Document

>>> doc_1 = Document.create("/doc-1.xml", "<root>1</root>")
>>> doc_2 = Document.create("/doc-2.xml", "<root>2</root>")

>>> mgr = MLClientManager("local")
>>> with mgr.get_client("app-services") as ml:
...     with ml.transaction() as txn:
...         ml.documents.write([doc_1, doc_2], **txn)
...         ml.eval.xquery('xdmp:document-insert("/doc-3.xml", <root>3</root>)', **txn)
...     # all three inserts commit together here, on the clean exit
```

Opened against a specific database, `**txn` carries the database too:

```python
>>> with mgr.get_client("app-services") as ml:
...     with ml.transaction(database="Documents") as txn:
...         ml.documents.write(doc_1, **txn)
...         ml.documents.read("/doc-1.xml", **txn)
```

## Roll back on error

If anything in the block raises, the transaction rolls back on the way out - even an operation that already succeeded never becomes visible:

```python
>>> with mgr.get_client("app-services") as ml:
...     with ml.transaction() as txn:
...         ml.documents.write(doc_1, **txn)
...         ml.documents.read("/missing.xml", **txn)   # raises RESTAPI-NODOCUMENT
...     # the read raised, so the block exits with an error and rolls back:
...     # doc_1 was never written
```

## Read transaction details

```python
>>> with mgr.get_client("app-services") as ml:
...     with ml.transaction(database="Documents") as txn:
...         txn.id           # the server-assigned transaction id
...         txn.database     # the database it was opened against, or None
...         txn.status()     # {'transaction-status': {...}}
```

## Manual commit and rollback

Without a `with` block you own the lifecycle - commit or roll back yourself:

```python
>>> with mgr.get_client("app-services") as ml:
...     txn = ml.transaction()
...     try:
...         ml.documents.write(doc_1, **txn)
...         txn.commit()
...     except Exception:
...         txn.rollback()
...         raise
```
