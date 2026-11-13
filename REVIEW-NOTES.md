# Review notes - feature/v1-14-auth-session-logging

## Items

- C8. Ad-hoc session warning on every request
- C9. Digest/basic on an `application-level` server never sends credentials

## Original plan

### C8

  - Decision: do - DEBUG on every request. The supported mode does not warn.
    - `clients/http.py:604` (`HttpClient`) and `:993` (`AsyncHttpClient`): `logger.warning(...)` ->
      `logger.debug(...)`, same message.
    - Docs (`docs/advanced/connections.md`, the client lifecycle section): add one sentence that each request
      outside `with` / `connect()` opens a new connection (and, with digest, a new auth handshake), so loops of
      many requests should use `with MLClient(...)` or `connect()`.
    - Test: an unconnected request logs nothing at WARNING and the message at DEBUG.

### C9

  - Decision: do - docs and a debug log.
    - Docs (`docs/advanced/connections.md`, the auth section): digest sends credentials only after a 401
      challenge; an `application-level` App Server never sends one, so every request runs as the server's default
      user. Use `auth=None` on purpose for such servers, or `basic` when the credentials must be sent.
    - Code: a small `httpx.DigestAuth` subclass used for `digest` / `digestbasic` (`auth.py` `_build_auth`); in
      `auth_flow`, when the first response is not a 401 challenge, `logger.debug("Digest credentials were not
      requested by the server - the request ran without them (%s %s)", method, url)`. No WARNING (C8: a supported
      setup must not warn on every request).
    - Test: against a server that never answers 401 the debug line appears and no `Authorization` header is sent;
      against a digest challenge no such line.
    - Prototype, verified 2026-11-13 (server that never answers 401: one debug line per request, sync and async;
      local MarkLogic digest on 8000: 204 twice, no line). It wraps httpx's own flow and reads no private
      attributes; httpx runs `auth_flow` for `AsyncClient` too:
      ```python
      class _ChallengeAwareDigestAuth(httpx.DigestAuth):
          """Digest auth that reports when the server never asks for credentials."""

          def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
              digest_flow = super().auth_flow(request)
              outgoing = next(digest_flow)
              while True:
                  response = yield outgoing
                  if _ran_without_credentials(outgoing, response):
                      logger.debug(
                          "Digest credentials were not requested by the server - "
                          "the request ran without them (%s %s)",
                          outgoing.method,
                          outgoing.url,
                      )
                  try:
                      outgoing = digest_flow.send(response)
                  except StopIteration:
                      return


      def _ran_without_credentials(request: httpx.Request, response: httpx.Response) -> bool:
          return "Authorization" not in request.headers and response.status_code != httpx.codes.UNAUTHORIZED
      ```
      After the first challenge httpx sends `Authorization` pre-emptively, so a normal digest server logs nothing.

## What was added or changed around it

- The prototype is integrated as is, with project conventions applied: multi-line signatures and docstrings,
  `Generator` imported under `TYPE_CHECKING`, the class placed below its only caller (`_build_from_shortcut`)
  and its helper `_ran_without_credentials` below the class.
- The C9 docs paragraph also names the logger (`mlclient.auth`) where the DEBUG line appears and notes that
  basic sends credentials with every request.
- The `Request details` debug line of the HTTP client now prints `auth [_ChallengeAwareDigestAuth]` instead of
  `auth [DigestAuth]` for digest. `isinstance(..., httpx.DigestAuth)` still holds, so no public behaviour or
  existing test changed.
- No changelog entry: the repository has no changelog file.

## Report

- Behaviour:
  - `HttpClient` / `AsyncHttpClient`: the "is not connected -- A request will be sent in an ad-hoc initialized
    session (METHOD endpoint)" message is now DEBUG instead of WARNING (same text).
  - `auth="digest"` / `"digestbasic"` now build `_ChallengeAwareDigestAuth` (an `httpx.DigestAuth` subclass).
    When a request without `Authorization` is answered with anything but 401, it logs at DEBUG on
    `mlclient.auth`: "Digest credentials were not requested by the server - the request ran without them
    (GET http://host:port/path)". Once a server has challenged, httpx sends `Authorization` pre-emptively and
    nothing is logged. No public API change.
- Docs: `docs/advanced/connections.md` - a paragraph on digest vs `application-level` servers in
  "Authentication methods", and a sentence on short-lived sessions (new connection and digest handshake per
  request; use `with` or `connect()` for many requests) in "API tiers on separate connections".
- Files: `mlclient/auth.py`, `mlclient/clients/http.py`, `docs/advanced/connections.md`,
  `tests/unit/mlclient/clients/test_http.py`, `tests/unit/mlclient/clients/test_async_http.py`.
- Tests (each in the sync and async client test file, respx-mocked):
  - an unconnected request logs the ad-hoc message once at DEBUG and nothing at WARNING or above;
  - digest against a server that never answers 401: no `Authorization` header sent, exactly the DEBUG line;
  - the same for `digestbasic`;
  - two unchallenged requests log two lines;
  - a normal digest challenge (401, then 200 twice): `Authorization` on the retry and the next request, no line.
- Results: full unit suite 10435 passed (serial run). Under `pytest -n auto` 3 CLI tests
  (`test_ml_client_application.py::test_main_sys_exit_1`, two in `test_env_show_command.py`) failed once and
  pass when run serially; they do not touch the changed code. Ruff check and format clean for touched files.
  `mkdocs build --strict` succeeds.
- No integration tests were requested or added.
- Verified against local MarkLogic 12.1 with the worktree code:
  - port 8000 (digest server), sync unconnected, sync connected x2, async `digestbasic`: 204, `Authorization`
    sent, no digest line; the unconnected request logged the ad-hoc message at DEBUG.
  - port 3693 (`application-level` server): 204, no `Authorization` sent, one digest DEBUG line per request in
    sync and async clients.

## Open points for the reviewer

- None.
