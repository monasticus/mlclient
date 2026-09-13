# Evaluate code

**Evaluate code from a file**

```python
>>> from mlclient import MLClientManager

>>> mgr = MLClientManager("local")
>>> with mgr.get_client() as ml:
...     result1 = ml.eval.file("./xqy-code-to-eval.xqy")
...     result2 = ml.eval.file("./js-code-to-eval.js")
```

**Evaluate raw xquery code**

```python
>>> from mlclient import MLClientManager

>>> with MLClientManager("local").get_client() as ml:
...     result = ml.eval.xquery("fn:current-dateTime()")
>>> result
datetime.datetime(2024, 2, 22, 11, 38, 32, 709484, tzinfo=datetime.timezone.utc)
```

**Evaluate raw javascript code**

```python
>>> from mlclient import MLClientManager

>>> with MLClientManager("local").get_client() as ml:
...     result = ml.eval.javascript("fn.currentDateTime()")
>>> result
datetime.datetime(2024, 2, 22, 11, 39, 22, 264102, tzinfo=datetime.timezone.utc)
```

**Evaluate code with variables**

```python
>>> from mlclient import MLClientManager

>>> xq = '''
... declare variable $DAYS external;
...
... fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'''

>>> with MLClientManager("local").get_client() as ml:
...     result = ml.eval.xquery(
...         xq,
...         variables={"DAYS": 5},
...     )
>>> result
datetime.datetime(2024, 2, 17, 12, 17, 49, 556376, tzinfo=datetime.timezone.utc)
```

```python
>>> from mlclient import MLClientManager

>>> xq = '''
... declare variable $DAYS external;
...
... fn:current-dateTime() - xs:dayTimeDuration("P" || $DAYS || "D")'''

>>> with MLClientManager("local").get_client() as ml:
...     result = ml.eval.xquery(
...         xq,
...         DAYS=5,
...     )
>>> result
datetime.datetime(2024, 2, 17, 12, 19, 45, 225135, tzinfo=datetime.timezone.utc)
```

**Evaluate code with variables within a namespace**

```python
>>> from mlclient import MLClientManager

>>> xq = '''
... declare variable $local:DAYS external;
...
... fn:current-dateTime() - xs:dayTimeDuration("P" || $local:DAYS || "D")'''

>>> with MLClientManager("local").get_client() as ml:
...     result = ml.eval.xquery(
...         xq,
...         variables={
...             "{http://www.w3.org/2005/xquery-local-functions}DAYS": 5,
...         },
...     )
>>> result
datetime.datetime(2024, 2, 17, 12, 21, 28, 547853, tzinfo=datetime.timezone.utc)
```

**Evaluate code on a custom database**

```python
>>> from mlclient import MLClientManager

>>> with MLClientManager("local").get_client() as ml:
...     result = ml.eval.xquery(
...         "xdmp:database() => xdmp:database-name()",
...         database="Documents",
...     )
>>> result
'Documents'
```

**Evaluate code and get raw data**

```python
>>> from mlclient import MLClientManager

>>> with MLClientManager("local").get_client() as ml:
...     result = ml.eval.xquery("fn:current-dateTime()", output_type=str)
>>> result
'2024-02-22T12:24:40.362014Z'
```

```python
>>> from mlclient import MLClientManager

>>> with MLClientManager("local").get_client() as ml:
...     result = ml.eval.xquery("fn:current-dateTime()", output_type=bytes)
>>> result
b'2024-02-22T12:24:53.677793Z'
```
