# Transactions

A multi-statement transaction groups several document or eval operations so they commit or roll back as a unit. Open one with `ml.transaction()`; the returned `TransactionService` is a context manager that commits on a clean exit and rolls back if the block raises.

Spread it with `**` into any content operation to run that operation inside the transaction - it unpacks to `txid` (and `database`, when the transaction was opened against one).

## Commit on clean exit

```python
>>> from mlclient import MLClient
>>> from mlclient.models import Document

>>> doc_1 = Document.create("/doc-1.xml", "<root>1</root>")
>>> doc_2 = Document.create("/doc-2.xml", "<root>2</root>")

>>> with MLClient() as ml:
...     with ml.transaction() as txn:
...         ml.documents.write([doc_1, doc_2], **txn)
...         ml.eval.xquery('xdmp:document-insert("/doc-3.xml", <root>3</root>)', **txn)
...     # all three inserts commit together here, on the clean exit
```

Opened against a specific database, `**txn` carries the database too:

```python
>>> with MLClient() as ml:
...     with ml.transaction(database="Documents") as txn:
...         ml.documents.write(doc_1, **txn)
...         ml.documents.read("/doc-1.xml", **txn)
```

## Roll back on error

If anything in the block raises, the transaction rolls back on the way out - even an operation that already succeeded never becomes visible:

```python
>>> with MLClient() as ml:
...     with ml.transaction() as txn:
...         ml.documents.write(doc_1, **txn)
...         ml.documents.read("/missing.xml", **txn)   # raises RESTAPI-NODOCUMENT
...     # the read raised, so the block exits with an error and rolls back:
...     # doc_1 was never written
```

## Read transaction details

```python
>>> with MLClient() as ml:
...     with ml.transaction(database="Documents") as txn:
...         txn.id           # the server-assigned transaction id
...         txn.database     # the database it was opened against, or None
...         txn.status()     # {'transaction-status': {...}}
```

## Manual commit and rollback

Without a `with` block you own the lifecycle - commit or roll back yourself:

```python
>>> with MLClient() as ml:
...     txn = ml.transaction()
...     try:
...         ml.documents.write(doc_1, **txn)
...         txn.commit()
...     except Exception:
...         txn.rollback()
...         raise
```

## What `ml.transaction()` returns and how `**txn` works

`ml.transaction()` opens a server-side transaction (a `POST /v1/transactions`
request) and returns a
[TransactionService][mlclient.services.TransactionService] bound to
its id. It exposes:

- `txn.id` - the server-assigned transaction id.
- `txn.database` - the database it was opened against, or `None`.
- `txn.status()` - the raw status document from the server.
- `txn.commit()` and `txn.rollback()` - end the transaction manually.
- context-manager entry and exit - commit on a clean exit, roll back on an error.

`**txn` works because the service is a mapping: it exposes `txid`, and
`database` only when the transaction was opened against one. Spreading it into a
call passes exactly the keyword arguments that bind that call to the
transaction. Opened without a database, `**txn` yields just `txid`, so it never
passes `database=None` into an operation that has its own default database.
