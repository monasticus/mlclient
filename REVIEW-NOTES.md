# Review notes - feature/v1-11-tls-client-cert

## Items

- C1. `verify: false` drops the client certificate

## Original plan

Decision: do as proposed. In `_get_ssl_context` / `_build_ssl_context` (`connection.py:333-363`): when
`verify is False` and `cert_file` is set, return a cached context built with `ssl.create_default_context()`,
`check_hostname = False`, `verify_mode = ssl.CERT_NONE` and `load_cert_chain(cert_file, key_file,
key_password)`. `verify=False` without `cert_file` stays `None` -> httpx `verify=False`, as today. The same
context also reaches the Cloud token flow through `_transport_verify`. Test: the unit test checks the
context (`verify_mode`, `check_hostname`, a loaded chain); optionally an integration test with a local
TLS server requiring a client certificate.

## What was added or changed around it

- No integration test. `tests/integration` runs against the project's docker MarkLogic only; a test that
  spawns `openssl s_server` does not fit that pattern (extra binary on CI, port management). Instead, the
  "loaded chain" part of the unit test is a real TLS handshake over `ssl.MemoryBIO` between the mlclient
  context and a stdlib server context that requires a client certificate: it asserts the server received the
  client certificate. That covers what the integration test would have proven, without a network or server.
- The manual end-to-end verification with `openssl s_server` is described in the Report.

## Report

- Behaviour: `SSLConfig(verify=False, cert_file=..., key_file=...)` now presents the client certificate
  (mutual TLS) while skipping server certificate and hostname checks. `verify=False` without `cert_file` is
  unchanged (`_get_ssl_context` returns `None`, httpx gets `verify=False`). No public API change.
- Files: `mlclient/connection.py` (`_get_ssl_context`, `_build_ssl_context`),
  `tests/unit/mlclient/test_connection.py`.
- Tests added (both red before the fix, green after):
  - `test_get_ssl_context_verify_false_with_client_cert_skips_server_checks` - `check_hostname is False`,
    `verify_mode == CERT_NONE`, context is cached.
  - `test_get_ssl_context_verify_false_presents_client_cert` - in-memory handshake; the server sees the client
    certificate subject.
- Unit suite: 10427 passed. Ruff check and format clean for the touched files.
- Manual verification (no known environment uses client certificates): in a temp dir, a test CA, a self-signed
  server certificate and a client certificate signed by the CA; `openssl s_server -accept 18611 -Verify 1
  -verify_return_error -CAfile ca.pem -www`; client `httpx.get(..., verify=_get_ssl_context(SSLConfig(verify=False,
  cert_file=..., key_file=...)) or False)`:
  - before (main): `ReadError [SSL: TLSV13_ALERT_CERTIFICATE_REQUIRED]`, server log "peer did not return a
    certificate";
  - after (this branch): `200`, server log shows the client certificate `CN = c1-client` verified.
- Integration tests: none added, none run.

## Open points for the reviewer

- None.
