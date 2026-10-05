# Configuration and environment discovery

## Choose project or personal scope

Use project `.mlclient/mlclient-NAME.yaml` for an application checkout. Use
`~/.mlclient/mlclient-NAME.yaml` for personal ad hoc CLI work and reusable scripts
launched outside a project. `ml env … --global` targets home explicitly.
Normal discovery walks from cwd through parents and stops at the first
`.mlclient` directory; it does not merge project/global files or search a second
directory when the chosen directory lacks the requested environment. Launch
personal server commands under home so its `.mlclient` is an ancestor, or load
the global YAML explicitly in a script. `--global` belongs to environment and
installation commands; it is not a universal server-command option.

```sh
ml env show
ml env show dev --defaults
ml env show dev content --defaults
ml env show --global
ml env init dev
ml env init personal --global
ml env copy dev dev-alt --edit
ml env edit dev
```

Identify the actual directory in Python without reading secrets:

```python
from pathlib import Path
from mlclient.env import find_mlclient_directory

config_dir = find_mlclient_directory(Path.cwd())
config_file = config_dir / 'mlclient-dev.yaml'
```

Use `ml env show dev --raw` only when verbatim comments are needed; it reveals
credentials. Use `ml env edit` or a focused text edit for commented alternate
credentials. A YAML parser drops comments; writing its output can destroy the
operator's alternatives. Prefer a separate named environment or runtime override
for alternate accounts. Keep copied secrets out of generated output and commits.

## Minimal environment

```yaml
app-name: example
host: localhost
protocol: http
username: my-user
password: REPLACE_LOCALLY
auth: digest
app-servers:
  - id: content
    port: 8100
    rest: true
```

The environment also provides `app-services` (8000), `manage` (8002), `admin`
(8001) and `health` (7997) defaults. Explicit entries with those identifiers
replace their connection defaults. Select content explicitly if its REST server
isn't the default. Root settings inherit into servers; server-specific connection
and SSL fields override them. YAML holds connection/auth data, not runtime
`retry`, `timeout` or `limits`. Consult the environment schema for TLS, OAuth,
certificate and Cloud settings instead of inventing YAML keys or interpolation.
MLClient does not expand shell `${VAR}` placeholders in this example.

```python
from mlclient import MLClientManager
from mlclient.env import MLEnvironment

manager = MLClientManager('dev')
with manager.get_client('content') as ml:
    print(ml.version)

# Inspect a file from a specific directory without changing process cwd.
environment = MLEnvironment.load_file('/path/to/mlclient-dev.yaml')
manager.config = environment
```

`manager.config` returns a copy. Assign changes back to affect later client
factories; this does not update the YAML or already-open clients.
Factories configure auxiliary Manage/Admin/Health connections too. Raw `.http`
uses the selected primary connection; `.manage` uses Manage independently.
Numeric CLI `-c 8100` overrides the default REST connection's port; it does not
perform App Server discovery. Logs `--server` means a log target, not `--connection`.

## Runtime policies

```python
import httpx
from httpx_retries import Retry
from mlclient import MLClientManager

manager = MLClientManager('dev')
ml = manager.get_async_client(
    'content',
    timeout=httpx.Timeout(30, connect=5, pool=5),
    limits=httpx.Limits(max_connections=8, max_keepalive_connections=8),
    retry=Retry(total=2, backoff_factor=0.5, allowed_methods=['GET', 'HEAD']),
)
```

Use an async context manager around `ml`. Pool limits bound active connections;
they do not cap created tasks. Batch/chunk requests separately. A per-request
`timeout=5` overrides only that request and each subrequest of a service.
An overall deadline must wrap the whole coroutine (`asyncio.wait_for` on Python
3.10; `asyncio.timeout` on 3.11+).

- Ordinary timeout defaults: connect/pool 5s, read/write 60s. Health has its own
  5s defaults and no retries unless explicitly overridden.
- `timeout=None` disables every HTTP timeout. Omitted/`UNSET` inherits.
- `retry=0` disables retries; `retry=None` restores the selected tier's default.
  Ordinary default permits up to five retries with backoff 0.5, subject to method,
  status and exception eligibility. Do not enable automatic replay of mutations
  without checking idempotency and uncertain outcomes after network failures.
- Manager overrides apply to all tiers; factory overrides affect the primary
  selected connection. Prefer factory policies when health must remain fast.
- `HTTPConfig.resolve(...)` constructs config; `config.clone(...)` changes a
  resolved config. Supplying `config=` takes precedence over separate kwargs.
- Keep TLS verification enabled. Use `SSLConfig` for CA/client certificates;
  `AuthConfig` or native auth handlers for advanced auth. Kerberos needs its own
  optional dependency; skill installation does not.

Read the installed public signatures and
[MLClient environment guide](https://monasticus.github.io/mlclient/user/environments/),
[connections](https://monasticus.github.io/mlclient/user/python/connections/) and
[HTTP configuration](https://monasticus.github.io/mlclient/user/http-configuration/).
