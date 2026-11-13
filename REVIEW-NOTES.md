# Review notes - feature/v1-12-retry-policy

## Items

- C2. Default retry retries `ReadTimeout`

## Original plan

- Decision: do - drop `ReadTimeout` and status 504 from the default retry; everything else stays retried.
  - `DEFAULT_RETRY_STRATEGY` (`mlclient/http.py:40`):
    ```python
    Retry(
        total=5,
        backoff_factor=0.5,
        retry_on_exceptions=[
            httpx.ConnectTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
            httpx.NetworkError,  # ConnectError, ReadError, WriteError, CloseError
            httpx.RemoteProtocolError,
        ],
        status_forcelist=[429, 502, 503],
    )
    ```
  - Unchanged: retried methods (HEAD, GET, PUT, DELETE, OPTIONS, TRACE; never POST), `total`, backoff,
    `_RESTART_RETRY_STRATEGY` (`clients/http.py:28`, waits for a restart, keeps timeouts and 504),
    `NO_RETRY_STRATEGY`, the health connection.
  - Accepted gap: an ALB 504 for "could not connect to the target within 10 s" (node down, not yet
    deregistered) is no longer retried; the user reruns. Opt back in with
    `MLClient(retry=Retry(..., status_forcelist=[429, 502, 503, 504]))`.
  - Document in the retry section of the docs (`docs/advanced/` / `docs/guides/clients.md`): what is retried,
    why a read timeout and 504 are not (the request is still running on the server), how to opt in.
  - Regression tests (local socket servers, as in the research): a reset connection (RST -> `ReadError`) and a
    close without a response (`RemoteProtocolError`) still give 6 attempts; a slow response (`ReadTimeout`) and
    a 504 give 1 attempt; 502/503 still retried.

## What was added or changed around it

- The numpy docstrings of `MLClient`, `AsyncMLClient` and `HttpClient` / `AsyncHttpClient` / the session
  clients said `default Retry(total=5, backoff_factor=0.5)`, which no longer describes the default. They now say
  `default DEFAULT_RETRY_STRATEGY`.
- The status list uses `httpx.codes` names (`TOO_MANY_REQUESTS`, `BAD_GATEWAY`, `SERVICE_UNAVAILABLE`), as
  `_RESTART_RETRY_STRATEGY` does; the values equal the decision's `[429, 502, 503]`.
- The docs (`docs/advanced/http/retries.md`, "Default policy") also state that the int shorthand
  (`retry=2` -> `Retry(total=2)`) uses the httpx-retries defaults and therefore still retries read timeouts and
  504 - see open points.
- Regression tests use one small threaded socket server on an OS-assigned port (port 0, no clashes with
  parallel runs) instead of respx, so the real httpcore mapping is exercised (RST -> `ReadError`, close without
  response -> `RemoteProtocolError`). Backoff sleeps are patched out; the module runs in about 1 s.

## Report

- Behaviour: `DEFAULT_RETRY_STRATEGY` retries `ConnectTimeout`, `WriteTimeout`, `PoolTimeout`, `NetworkError`
  (ConnectError, ReadError, WriteError, CloseError), `RemoteProtocolError` and statuses 429, 502, 503. A read
  timeout and a 504 now fail after one attempt. Methods, `total=5`, `backoff_factor=0.5`,
  `_RESTART_RETRY_STRATEGY`, `NO_RETRY_STRATEGY` and the health connection are unchanged.
- Files:
  - `mlclient/http.py` - the strategy, with a one-line comment on why ReadTimeout and 504 are excluded.
  - `mlclient/_client.py`, `mlclient/clients/http.py` - docstring defaults.
  - `docs/advanced/http/retries.md` - what is retried, why a read timeout and 504 are not, how to opt back in.
  - `tests/unit/mlclient/test_default_retry_strategy.py` - new.
- Tests (17 new, `tests/unit/mlclient/test_default_retry_strategy.py`):
  - socket server, GET through `HttpClient` with the default strategy: RST -> 6 requests received; close
    without response -> 6; slow response (read timeout 0.05 s) -> 1; 504 -> 1; 429 / 502 / 503 -> 6 each;
  - strategy level: each retried exception type is retryable, `ReadTimeout` is not, `POST` is not.
  - Red before the change: the read timeout, 504 and `ReadTimeout` checks failed; green after.
- Results: full unit suite 10442 passed; `ruff check` and `ruff format --check` clean on touched files;
  `mkdocs build --strict` passed.
- Local MarkLogic 12.1 (`local`, app server `scifinder-test`): a default client's GET `/v1/search` returns 200;
  the same GET with `read=0.001` raises `ReadTimeout` after 0.013 s (one attempt, no backoff). Integration tests
  were not added - the decision asks for socket-server regression tests, which run in the unit suite.

## Open points for the reviewer

- Int shorthand: `MLClient(retry=2)` (and `MLClientManager(..., retry=2)`) builds `Retry(total=2)` with the
  httpx-retries defaults, so it still retries `ReadTimeout` and 504 (and has no backoff). A user who only lowers
  the count silently gets the old behaviour back. Should `_normalize_retry` build the int shorthand with the
  default policy's exception and status lists (and possibly its backoff)? Left unchanged here because the
  decision does not cover it; only documented.
