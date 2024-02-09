Core
====

Clients
-------

Overview
^^^^^^^^

MLClient offers two types of clients to access a MarkLogic Server: high-level and low-level.
High-level clients are designed for specific endpoints, such as ``/v1/documents``.
They provide a simple and intuitive API that covers all the functionality of each endpoint.
Low-level clients are the foundation of MLClient. They use :class:`~mlclient.calls.ResourceCall` objects to represent the parameters of any endpoint.
You can use low-level clients to send raw requests to the server.
You can learn more about high-level and low-level clients in the following sections.