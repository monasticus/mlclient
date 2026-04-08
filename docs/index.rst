MLClient - MarkLogic instance in your hands
===========================================

.. image:: https://img.shields.io/badge/GitHub-monasticus%2Fmlclient-white?style=plastic&logo=github&color=white
    :target: https://github.com/monasticus/mlclient
    :alt: Tag Badge

.. image:: https://img.shields.io/github/license/monasticus/mlclient?label=License&style=plastic
    :target: https://github.com/monasticus/mlclient/blob/main/LICENSE
    :alt: License Badge

.. image:: https://img.shields.io/pypi/pyversions/mlclient?label=Python&style=plastic
    :target: https://www.python.org/
    :alt: Python Version Support Badge

A Python client for MarkLogic Server. Three API layers, async out of the box, CLI included.

.. code-block:: sh

    pip install mlclient

By default MLClient connects to ``localhost:8000`` with basic auth (``admin``/``admin``).
Pass ``host``, ``port``, ``username``, ``password``, or ``auth_method`` to override:

.. code-block:: python

    config = {
        "host": "ml.example.com",
        "port": 8040,
        "username": "my-user",
        "password": "my-password",
        "auth_method": "digest",
    }
    ml = MLClient(**config)

-------------------

Quickstart
----------

Evaluate XQuery and get a parsed Python object back - not raw multipart HTTP, not strings:

.. code-block:: python

    from mlclient import MLClient

    with MLClient() as ml:
        db_name = ml.eval.xquery("xdmp:database() => xdmp:database-name()")
        print(db_name)          # "Documents"
        print(type(db_name))    # <class 'str'>

        timestamp = ml.eval.xquery("fn:current-dateTime()")
        print(timestamp)        # 2024-06-21 14:08:32.130813+00:00
        print(type(timestamp))  # <class 'datetime.datetime'>

Read and write documents:

.. code-block:: python

    from mlclient import MLClient
    from mlclient.models import Document

    with MLClient() as ml:
        doc = ml.documents.read("/patient/record-1.json")
        print(doc.uri)       # /patient/record-1.json
        print(doc.content)   # {"name": "Smith", "id": "001"}

        new_doc = Document.create("/patient/record-2.json", {"name": "Jones", "id": "002"})
        ml.documents.write(new_doc)

Available high-level services:

==================  =====================  =======================================
Service             Endpoint               Description
==================  =====================  =======================================
``ml.documents``    ``/v1/documents``       Read, write, delete documents
``ml.eval``         ``/v1/eval``            Evaluate XQuery and JavaScript
``ml.logs``         ``/manage/v2/logs``     Retrieve and filter server logs
==================  =====================  =======================================


More control
------------

Need the raw ``httpx.Response``? Drop down to the mid-level API clients.
Use the built-in response parser when you want parsed results:

.. code-block:: python

    with MLClient() as ml:
        resp = ml.rest.eval.post(xquery="xdmp:database() => xdmp:database-name()")
        print(resp.status_code)         # 200
        parsed = ml.parser.parse(resp)  # "Documents"

Three mid-level API clients cover all of MarkLogic's API tiers:

- ``ml.rest`` -- REST Client API (``/v1/*``)
- ``ml.manage`` -- Management API (``/manage/v2/*``, port 8002)
- ``ml.admin`` -- Admin API (``/admin/v1/*``, port 8001)

.. code-block:: python

    with MLClient() as ml:
        resp = ml.manage.databases.get_properties("Documents", data_format="json")
        print(resp.json()["database-name"])  # Documents

        resp = ml.admin.get_timestamp()
        print(resp.text)  # 2024-06-21T14:08:32.130813Z

Port routing is automatic. Manage and Admin requests always go to ports 8002
and 8001 regardless of the main client port.


Full control
------------

Send any HTTP request directly:

.. code-block:: python

    with MLClient() as ml:
        resp = ml.http.post(
            "/v1/eval",
            body={"xquery": "xdmp:database() => xdmp:database-name()"},
        )
        print(resp.text)  # raw multipart/mixed response


Async
-----

``AsyncMLClient`` mirrors ``MLClient`` 1:1 - every method is a coroutine:

.. code-block:: python

    from mlclient import AsyncMLClient

    async with AsyncMLClient() as ml:
        db_name = await ml.eval.xquery("xdmp:database() => xdmp:database-name()")
        doc = await ml.documents.read("/patient/record-1.xml")
        resp = await ml.http.get("/manage/v2/servers")


CLI
---

.. code-block:: sh

    ml call eval -e local -x "xdmp:database() => xdmp:database-name()"
    ml call logs -e local -a 8002 --regex "XDMP-.*"

See :doc:`user/cli` for the full CLI reference.


.. toctree::
   :maxdepth: 1
   :caption: Python API:

   api/mlclient/mlclient

.. toctree::
   :maxdepth: 1
   :caption: User Guide:

   user/setup
   user/cli
   user/pythonapi



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
