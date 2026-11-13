# Review notes - feature/v1-18-manage-requests

## Items

- D4. GET `/manage/v2/requests`

## Original plan

- Decision: do - Call and API for the whole `requests` resource, in the same shape as `hosts`, `forests`,
  `databases`, `users` (`calls/hosts.py`, `api/hosts.py`).
  1. Calls in a new `mlclient/calls/requests.py`:
     - `RequestsGetCall(data_format=None, view=None, group_id=None, host_id=None, server_id=None,
       seconds_min=None, fullrefs=None)` -> `GET /manage/v2/requests`; validates `format` (xml, json, html) and
       `view` (default, schema), `seconds_min` non-negative number;
     - `RequestGetCall(request, data_format=None, group_id=None, host_id=None, server_id=None)` ->
       `GET /manage/v2/requests/{id|uri}`.
     Exported from `mlclient.calls` like the other resources.
  2. API in a new `mlclient/api/requests.py`: `RequestsApi.get_list(...)` and `RequestsApi.get(request, ...)`,
     plus `AsyncRequestsApi`, keyword-only parameters and `timeout`, named and documented like `HostsApi`
     (`get_list` / `get`); reached as `ml.manage.requests` through a cached property in `ManageApi` /
     `AsyncManageApi` (`api/manage.py`, next to `databases`, `hosts`).
  3. No service, no CLI command in this release.
  4. Docs: the Management API reference pages pick up the new module (API reference generation); the
     "client timeout" note of B6 mentions `ml.manage.requests.get_list(seconds_min=...)` to see what still runs.
  5. Tests: unit for both Calls (endpoint, params, validation) and both API classes (sync and async, the same
     pattern as the hosts tests); integration in the CI matrix - a slow eval (`xdmp:sleep`) appears in
     `get_list(seconds_min=1)` with its `request-text`, and `get(<idref>)` returns it.

## What was added or changed around it

The local MarkLogic 12.1 probes changed some details of the decision:

- `seconds_min` must be a **non-negative integer**, not any non-negative number. MarkLogic casts the value with
  `xs:integer($seconds-min)`. `seconds-min=1.5` and `seconds-min=abc` return `500 XDMP-CAST`, and
  `seconds-min=-1` returns `500 XDMP-CAST` from inside its duration code. The Call rejects floats, strings, bools
  and negative values with `WrongParametersError("The seconds_min parameter must be a non-negative integer")`.
  `0` is accepted and sent as `seconds-min=0`.
- The list `view` accepts `default`, `schema` **and `describe`**. The server's own error message for
  `view=status` reads "describe|default|schema". `describe` returned 200 on 12.1. The v10-v12 docs list only
  `default` and `schema`.
- The keyword is `full_refs`, not `fullrefs`. It matches the existing `ForestsGetCall` / `ServersGetCall`
  keyword. It is still sent as the `fullrefs` URL parameter, as `"true"`/`"false"`.
- Defaults follow the hosts/databases Calls (`data_format="xml"`, `view="default"`, and `None` resolves to
  them), so the default request sends `format=xml&view=default` like the other Manage list Calls. The API
  methods take `None` defaults, as decided.
- The decision lists the `get` parameters as `request, data_format, group_id, host_id, server_id`. These are
  the documented ones and nothing else was added. On 12.1 the detail endpoint also parses `view` and
  `fullrefs`, but the docs do not list them, so they are left out. `ml.manage.call(...)` covers them if needed.
- Docstrings record behaviour seen on the server. A `server_id` given by name requires `group_id`
  (`400 REST-REQUIREDPARAM` otherwise). `get()` on an id that is not running returns 200 with
  `properties: null`. No REST endpoint cancels a request.
- Docs: no CLI `timeout` page exists on this branch (B6 is on the CLI branch). The note therefore went to the
  library guide `docs/advanced/http/timeouts.md`, section "Server execution limits and total duration". It
  covers what an expired timeout means and `ml.manage.requests.get_list(seconds_min=...)` with a working
  snippet. The API reference picks up `RequestsApi` / `AsyncRequestsApi` / the Calls automatically from
  `__all__`.

## Report

- **Public API:** `mlclient.calls.RequestsGetCall` and `RequestGetCall` are new. So are
  `mlclient.api.RequestsApi` and `AsyncRequestsApi`, with `get_list(*, data_format, view, group_id, host_id,
  server_id, seconds_min, full_refs, timeout)` and `get(request, *, data_format, group_id, host_id, server_id,
  timeout)`. All parameters except `request` are keyword-only. They are reached as `ml.manage.requests`
  through a `cached_property` on `ManageApi` and `AsyncManageApi`. No service and no CLI.
- **Files:**
  - `mlclient/calls/requests.py` (new), `mlclient/calls/__init__.py`
  - `mlclient/api/requests.py` (new), `mlclient/api/__init__.py`, `mlclient/api/manage.py`
  - `docs/advanced/http/timeouts.md`
  - tests: `tests/unit/mlclient/calls/test_requests_get_call.py`, `tests/unit/mlclient/calls/test_request_get_call.py`,
    `tests/unit/mlclient/api/test_manage_api.py`, `tests/unit/mlclient/api/test_async_manage_api.py`,
    `tests/unit/mlclient/test_public_api.py`
  - fixtures `tests/resources/unit/mlclient/api/test-{,async-}manage-api/test-get-request{,s}.json`
  - `tests/integration/mlclient/clients/test_api_wrappers.py` (`TestRequestsManagement`)
- **Fixtures** are real 12.1 responses captured during a running `xdmp:sleep` eval. The list response was
  trimmed to the test's own request: another user's request and its relations were removed, and the counts and
  summary were adjusted to one item.
- **Unit tests:** Calls cover the endpoint, method, params, Accept headers per format, view and format
  validation, `seconds_min` validation (-1, 1.5, "1", True), `0` sent, and `full_refs` true/false. API tests,
  sync and async, cover a recorded list and detail response, every parameter plus `timeout` forwarded
  (None / number / `httpx.Timeout`), a raw error response, and an invalid `seconds_min` rejected before any
  request. Full suite run serially: **10477 passed, coverage 100.00%**. Ruff check and format are clean on
  the touched files.
- **Integration:** `TestRequestsManagement` starts an 8 s `xdmp:sleep` eval in its own client thread. It polls
  `get_list(data_format="json", seconds_min=1)` until the request appears (checking `request-text`, kind `eval`
  and `update` false), then checks it through `get(idref)`. A second test checks the list views
  `default`/`schema`/`describe` (XML). **Not run locally.** CI runs them on 10.0-11.1, 11.3.7 and 12.1.
- **Live verification (local MarkLogic 12.1, worktree code):** a background `xdmp:sleep(15000)` eval appeared
  in `ml.manage.requests.get_list(data_format="json", seconds_min=1, group_id="Default",
  server_id="scifinder")` with its `request-text` and `update: false`. `get(idref)` returned its properties,
  and so did the async twin. The XML default works. A missing id returns 200 / `properties: null`. The docs
  snippet runs as written. `mkdocs build --strict` and `scripts/check_docs.py` pass.

## Follow-up code review (2026-11-13)

### Encode request URIs as a path segment

RequestGetCall accepts an ID or URI but interpolated the URI into the path without encoding. Reserved characters could change the request path, query or fragment. Encode the one segment with urllib.parse.quote as ValuesGetCall already does; a regression failed before the fix and passes after it. TestRequestsManagement: 4 integration tests passed on both local MarkLogic 10.0-11 and 12.1.0, including describe view.

## Open points for the reviewer

- `view="describe"` on the list endpoint is not documented but 12.1 accepts it. The integration test will show
  whether 10/11 accept it too. If not, drop it from `_SUPPORTED_VIEWS`.
- `full_refs` instead of the decision's `fullrefs` (follows the existing Calls). Confirm.
- When the CLI branch (B6) adds its timeout message and CLI docs, it can point to
  `ml.manage.requests.get_list(seconds_min=...)` or to the timeouts guide section added here.
