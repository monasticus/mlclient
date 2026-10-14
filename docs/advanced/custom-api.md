# Extend the client for your application

Suppose your MarkLogic HTTP App Server exposes `GET /app/tasks?status=open`
and returns `{"tasks": [{"title": "Review imports"}]}`. This is an example
application contract, not an endpoint installed by MLClient.

You can call it immediately with `ml.http.get("/app/tasks", params={"status": "open"})`.
For repeated use, extend the same two layers MLClient already gives you: add the
endpoint to the REST API so `ml.rest.tasks` returns the raw HTTP response, and
add a service so `ml.tasks` returns parsed Python. The existing public
interfaces already support this; no library internals or global registration
are needed.

## Follow the request through the layers

1. `TasksGetCall` describes the path, query and accepted response type.
2. `TasksApi` exposes a named method returning the raw response.
3. `AppRestApi` subclasses `RestApi`, adding `tasks` beside the built-in
   `eval`, `documents` and `transactions` - so `ml.rest.tasks` joins them.
4. `TasksService` calls `rest.tasks`, checks the status and parses the body -
   it builds on the API tier, just as the built-in `ml.eval` service builds on
   `ml.rest.eval`.
5. `AppClient` overrides `rest` to build `AppRestApi` and adds `tasks` as the
   parsed service on top of it - both sharing the client's connection and
   lifecycle.

```python
--8<-- "examples/custom_api.py"
```

Save this as `custom_api.py` in your application, then use it just like MLClient.
The API layer speaks HTTP; the service layer returns Python:

```python
from custom_api import AppClient

with AppClient(port=8100) as ml:
    response = ml.rest.tasks.list(timeout=5)  # raw httpx.Response
    response.raise_for_status()

    print(ml.tasks.open_titles(timeout=5))    # parsed list of titles
```

`ml.rest.tasks.list()` gives you the status code, headers and body to handle
yourself - the same contract as `ml.rest.eval` or `ml.rest.documents`.
`ml.tasks.open_titles()` sits above it, doing the parsing and error handling for
you. Reach for the service by default; drop to `ml.rest.tasks` when you need the
raw response.

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
sending and service methods become async. Inside a coroutine:

```python
from custom_api import AsyncAppClient

async def titles(password):
    async with AsyncAppClient(port=8100, username="my-user", password=password) as ml:
        return await ml.tasks.open_titles()
```

The two layers mirror MLClient itself: the API tier returns HTTP responses and
the service tier returns parsed values. See [Services](services.md) for how the
built-in services build on the API tiers. The example is exercised against
mocked HTTP responses by the documentation-example tests, including timeout
forwarding and server failures.
