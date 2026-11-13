# Review notes - feature/v1-13-config-validation-secrets

## Items

- C3. Secrets visible in `repr`
- C6. Env validation messages
- C7. OAuth without a token sends `Bearer None`

## Original plan

### C3

  - Decision: do - `SecretStr` + hidden error input (breaking, accepted before 1.0).
    - Fields become `SecretStr` / `Optional[SecretStr]`: `MLEnvironment.password`, `MLServerConfig.password`
      (`env.py:95,139`), `SSLConfig.key_password` (`connection.py:45`), `CloudConfig.api_key`
      (`connection.py:58`), `AuthConfig.token` (`auth.py:78`). Inputs stay plain strings (YAML and constructors
      accept `str`; pydantic wraps them).
    - Every internal read unwraps with `.get_secret_value()` at the point of use (8 reads in `connection.py`,
      `auth.py`, `http.py`, `env.py`, `cli/commands/env_init.py`); the unwrapped value is passed straight to
      httpx / ssl / auth handlers, never stored in another plain field.
    - `ml env show -s`: the reveal path unwraps `SecretStr` explicitly (`cli/commands/_env_common.py:165,191`);
      without `-s` the masking stays as today.
    - The same five models get `model_config = ConfigDict(hide_input_in_errors=True)` (merged with an existing
      `model_config`, e.g. `CloudConfig.populate_by_name`), so a `ValidationError` names the field and the reason
      without `input_value`.
    - Tests: `repr`, `str`, `model_dump_json` of each model show no secret; a `ValidationError` on a typo'd key
      shows no secret; `ml env show -s` still reveals; a client still authenticates (digest/basic, cert key
      password, Cloud api key, OAuth token).
    - Changelog: the type change of these public fields and `.get_secret_value()`.

### C6

  - Decision: do all of it.
    1. `extra="forbid"` on `MLEnvironment`, `MLServerConfig`, `SSLConfig`, `CloudConfig`, `AuthConfig` - an
       unknown key is an error with its field path.
    2. Every load failure of an environment file raises one `ConfigError` naming the file, one line per problem
       (`<field path>: <reason>`), no pydantic URL, no input values (C3). E.g.
       ```
       Invalid environment configuration in /home/u/.mlclient/mlclient-staging.yaml:
         app-servers.0.prot: unknown setting
         app-servers.0.port: Input should be a valid integer
       ```
    3. An empty file is an error (`Environment configuration file is empty: <path>`), not `{}` with defaults.
    4. No such server: list the available ids with their effective ports (predefined defaults resolved), in
       configuration order. Library (`NoSuchAppServerError` from `MLEnvironment` / `MLClientManager`,
       `env.py:283`, `_manager.py:508`):
       `There's no [restt] app server configuration in the [staging] environment. Available: rest (8010), manage (8002), app-services (8000), admin (8001), health (7997).`
       The CLI (`-c`) adds one line: `Pass a configured id or a port number to -c, e.g. -c 8010.`
    5. `auth` is validated when the file is loaded (a model validator on the shortcut / `AuthConfig.method`), so a
       typo like `digets` lands in the same file-named `ConfigError` instead of a `ValueError` at `get_client`.

### C7

  - Decision: do - a missing token is a configuration error, checked when the configuration is built.
    - A model validator on `AuthConfig` (`auth.py:78`): `method == "oauth"` with `token` missing or empty raises
      a validation error `token: required for method 'oauth'`; loaded from a file it lands in the file-named
      `ConfigError` of C6, built in Python (`MLClient(auth=AuthConfig(method="oauth"))`) it raises at construction.
    - `_build_from_config` (`auth.py:423`) no longer needs its own check. Test: no token and an empty token both
      fail; a token still sends `Authorization: Bearer <token>`.

## What was added or changed around it

- **Auth validation at load (C6.5), how.** The environment's `auth` field validates the setting
  itself (`env.py` `_validate_auth`): a string must be a known shortcut, a mapping is validated as
  `AuthConfig` there rather than by the `Union[str, AuthConfig]`, so a mistake is reported once under
  `auth...` instead of once per union member (pydantic otherwise prints an `auth.str` and an
  `auth.AuthConfig` error for every mapping problem). The shortcut check is shared with the client
  path (`auth._require_known_shortcut`), so the message is the same as for `MLClient(auth="digets")`.
- **`AuthConfig.method` is now `Literal["oauth", "kerberos", "certificate"]`.** Needed for "auth
  validated at load" to cover `auth: {method: saml}`. `AuthConfig(method="saml")` now raises a
  `ValidationError` at construction instead of a `ValueError` from `_build_from_config`; that
  unreachable branch was removed.
- **C7 is a field validator on `token`, not a model validator.** It produces the decided message
  `token: required for method 'oauth'` with the location on the field (`auth.token: ...`,
  `app-servers.0.auth.token: ...`) instead of on the whole `auth` mapping. `validate_default=True`
  makes it run when the token is omitted.
- **Every load failure is a `ConfigError`** - also invalid YAML (`Invalid YAML in environment
  configuration file: <path>`, without the parser's message, which quotes the offending line and
  could show a password) and a non-mapping file (`Environment configuration must be a mapping:
  <path>`). A file containing only comments counts as empty. The original `ValidationError` is
  not chained (`from None`), so a traceback cannot show the pydantic URL or input either.
- **Effective port.** `MLEnvironment._effective_port` now serves both `provide_config_dict` (which
  used `setdefault`) and the "no such server" message, so the listed port is exactly the one a
  client would use (Cloud: 443).
- **Without an environment name.** `MLEnvironment.provide_config(...)` does not know the file's
  name, so its message omits "in the [<env>] environment"; the manager (and so the CLI) includes
  it.
- **CLI `-c` hint**: the example port is the first configured server's effective port (the first
  listed id in the message), e.g. `-c 8010` for the decision's example.
- **`ml env show` / `ml env compare`.** Model dumps are taken in Python mode and every `SecretStr`
  unwrapped in `effective_config` (`_env_common._revealed`); masking without `-s` is still done at
  render time by key name. This also keeps `env compare` correct: comparing masked
  `**********` values would have hidden a password difference.
- **`ml env init --from-gradle`** validation errors no longer contain the password from
  `gradle.properties` (side effect of `hide_input_in_errors`).
- **Changelog**: the repository has no changelog file and no convention for one, so the breaking
  changes are listed here and documented in the docs (see Report) - see open points.

## Report

**Behaviour / public API (breaking, accepted before 1.0)**

- `MLEnvironment.password`, `MLServerConfig.password`, `SSLConfig.key_password`,
  `CloudConfig.api_key`, `AuthConfig.token` are `SecretStr` / `Optional[SecretStr]`; read with
  `.get_secret_value()`. Inputs (YAML, constructors) stay plain strings. `repr`, `str`, logs and
  `model_dump_json()` show `**********`. Unwrapped only at the point of use: digest/basic
  credentials (`env.py` root and per-server password into `HTTPConfig.resolve`), SSL key password
  (`connection._get_ssl_context`), Cloud API key (`connection._build_connection_auth`), OAuth token
  (`auth._build_from_config`). `HTTPConfig.password` stays a plain `str` (not in scope).
- The five models have `extra="forbid"` and `hide_input_in_errors=True`.
- `MLEnvironment.load` / `load_file` / `MLClientManager(...)` raise one `ConfigError` per load
  failure: file named, one `<field path>: <reason>` line per problem, `unknown setting` for unknown
  keys, no pydantic URL, no input values. Empty file is an error.
- `NoSuchAppServerError` lists the available ids with effective ports, in configuration order; the
  CLI adds `Pass a configured id or a port number to -c, e.g. -c <port>.`
- `AuthConfig(method="oauth")` without a token or with an empty token is a `ValidationError`.

**Files**: `mlclient/env.py`, `mlclient/auth.py`, `mlclient/connection.py`, `mlclient/_manager.py`,
`mlclient/exceptions.py` (docstring), `mlclient/cli/connection.py`,
`mlclient/cli/commands/_env_common.py`, `docs/advanced/more-on-environments.md` (new "Validation
errors" and "Secrets" sections, `provide_config_dict` note), `docs/advanced/connections.md`
(OAuth token required, `SecretStr` note, rejected-combinations row); tests below.

**Tests added / changed (unit)**

- `test_auth.py`: OAuth without / with empty token fails (`token` location, decided message); other
  methods need no token; OAuth config still sends `Authorization: Bearer <token>`; `repr` / `str` /
  `model_dump_json` hide the token; unknown key rejected without showing input; unknown method is a
  `ValidationError`.
- `test_connection.py`: `SSLConfig` / `CloudConfig` hide secrets; unknown keys rejected without
  showing input; an encrypted client key is unlocked with `key_password` (real `ssl.load_cert_chain`).
- `test_http_config.py`: Cloud token exchange posts the plain API key (respx).
- `test_env.py`: model secrets hidden; typo'd-key `ValidationError` hides the password; root and
  server passwords unwrapped into `HTTPConfig`; "no such server" message with effective ports
  (incl. Cloud 443); file-named multi-line `ConfigError` (exact text, no password, no URL, no
  chained cause); auth at load (`digets`, oauth without/empty token, unknown method, unknown key,
  per-server auth); unknown nested `ssl` / `cloud` keys; empty / comment-only / non-mapping /
  invalid YAML files.
- `test_manager.py`, `cli/test_cli_connection.py`: new messages incl. the `-c` hint (sync and async).
- Existing tests updated for `SecretStr` (`test_env.py` dumps, Cloud key, OAuth token).
- Existing `ml env show` tests (`-s` reveals password, OAuth token, key password, Cloud API key at
  root and per server; masked without `-s`) pass unchanged.

**Results**: `tests/unit` 10457 passed (serial run). Under `-n 8`
`cli/test_ml_client_application.py::test_main_sys_exit_1` fails, also on the base commit
`7fa179304`; it passes serially. `ruff check .` clean; `ruff format --check` clean for every file this branch touches (two unrelated test files, `cli/commands/test_http_command.py` and `test_invoke_command.py`, are already unformatted on the base and were left as they are).
`mkdocs build --strict` succeeds.

**Integration tests**: none added - `tests/integration/mlclient/connection/test_connection_matrix.py`
already authenticates with digest, basic, mutual TLS, double auth, OAuth (JWT) and Cloud (mocked
`/token`) through the changed code paths. Not run locally (CI runs them on 10.0-11.1, 11.3.7 and
12.1). The provisioned client key is not encrypted, so `key_password` is covered by the unit test
with a real encrypted key only.

**Verified against local MarkLogic 12.1 (worktree code, read-only)**

- Every environment file found (`tests/resources`, `dev/.mlclient`, `docs/guides/environments`,
  the home and repositories' `.mlclient` directories - 13 files) loads and resolves every server.
- `ml eval -e local -x '1+1'` -> `2` (digest); a per-server password override authenticates
  (digest on 8000); basic on 8000 gives 401 both here and on the base (the server is digest-only).
- `ml eval -c restt` lists ids with effective ports plus the `-c` hint; a scratch environment with
  `pasword` / `prot` / `port: abc`, an empty file and `auth: digets` each give the file-named
  `ConfigError` (exit code 1).

## Follow-up code review (2026-11-13)

### Do not echo invalid auth values

hide_input_in_errors does not remove user values embedded in a custom ValueError message. The shared auth-shortcut validator now lists allowed values without echoing the invalid input; a full-message regression protects a mistakenly pasted secret. Shared helpers imported across modules have non-private names and remain outside __all__. Focused affected suites: 802 passed; full unit suite: 10458 passed, 100% coverage.

## Open points for the reviewer

- No changelog exists in the repository; the breaking changes (five fields now `SecretStr`;
  `ConfigError` replaces `TypeError` / `ValidationError` / `yaml.YAMLError` on load;
  `AuthConfig.method` is a `Literal`; OAuth without token fails at construction; unknown keys
  rejected) should go into the 1.0.0 release notes.
- `ml env show` / `ml env compare` keep their own reading path (`read_config`): an empty file
  still shows defaults there and validation errors keep the existing
  `Invalid environment in <path>: check <fields>.` format (now also naming unknown keys). Should
  they share the new `ConfigError` message?
- Problems are listed in pydantic's order (server entries before root-level unknown keys), not
  sorted by file position.
