# Extend the client for your application

Suppose your MarkLogic HTTP App Server exposes `GET /app/tasks?status=open`
and returns `{"tasks": [{"title": "Review imports"}]}`. This is an example
application contract, not an endpoint installed by MLClient.

You can call it immediately with `ml.http.get("/app/tasks", params={"status": "open"})`.
For repeated use, give it a small API wrapper and a friendly operation on your
own client. The existing public interfaces already support this; no library
internals or global registration are needed.

## Follow the request through the layers

1. `TasksGetCall` describes the path, query and accepted response type.
2. `ApiClient` sends that description over an existing HTTP client.
3. `TasksApi` exposes a named method returning the raw response.
4. `AppClient.tasks` attaches the wrapper to the same connection and lifecycle.
5. `open_task_titles()` adds application-specific parsing and error handling.

```python
--8<-- "examples/custom_api.py"
```

Save this as `custom_api.py` in your application, then use it just like MLClient:

```python
from getpass import getpass
from custom_api import AppClient

with AppClient(port=8100, username="my-user", password=getpass()) as ml:
    print(ml.open_task_titles(timeout=5))
```

Port 8100 must serve your application endpoint. Built-in REST services only work
if that App Server also exposes their `/v1/*` routes. A custom route does not
make an arbitrary HTTP server a MarkLogic REST App Server.

## Keep transport configuration in one place

The extension wraps public `self.http`, so authentication, TLS, retry, timeout,
connection limits and cleanup remain owned by the parent client. A per-request
`timeout` is forwarded as an execution option, not a query parameter. Use a
separate configured client when the application lives on another host or needs
different credentials.

The async version shares the same Call, since a Call performs no I/O. Only the
sending and high-level methods become async. Inside a coroutine:

```python
from custom_api import AsyncAppClient

async def titles(password):
    async with AsyncAppClient(port=8100, username="my-user", password=password) as ml:
        return await ml.open_task_titles()
```

As your application grows, move related high-level operations into a service
object exposed through another property. There is no need for a service class
for a single short operation. The example is exercised against mocked HTTP
responses by the documentation-example tests, including timeout forwarding and
server failures.
