====
Core
====

Clients
=======

Overview
--------

MLClient offers two types of clients to access a MarkLogic Server: high-level and low-level.
High-level clients are designed for specific endpoints, such as ``/v1/documents``.
They provide a simple and intuitive API that covers all the functionality of each endpoint.
Low-level clients are the foundation of MLClient. They use :class:`~mlclient.calls.ResourceCall` objects to represent the parameters of any endpoint.
You can use low-level clients to send raw requests to the server.
You can learn more about high-level and low-level clients in the following sections.

High-level clients
------------------

High-level clients are designed for specific endpoints of MarkLogic Server and database.
They allow you to manage configuration or documents in MarkLogic with ease.
Each client ensures that you can perform all the operations in the corresponding area.
For example, some of the high-level clients are:

==========================================  ===================
Client                                      Endpoint
==========================================  ===================
:class:`~mlclient.clients.DocumentsClient`  ``/v1/documents``
:class:`~mlclient.clients.EvalClient`       ``/v1/eval``
:class:`~mlclient.clients.LogsClient`       ``/manage/v2/logs``
==========================================  ===================

DocumentsClient
^^^^^^^^^^^^^^^

EvalClient
^^^^^^^^^^

LogsClient
^^^^^^^^^^
