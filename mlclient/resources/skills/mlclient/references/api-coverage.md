# Choose and inspect the public Python API

Use the namespace map below to find the right abstraction. Check exact
signatures and docstrings in the **installed version** when writing code:

```python
import inspect
from mlclient import AsyncMLClient
from mlclient.services import AsyncCtsService

print(inspect.signature(AsyncCtsService.search))
print(inspect.getdoc(AsyncCtsService.search))
print(inspect.signature(AsyncMLClient))
```

Inspect the particular method/model needed, not the whole library. Public
namespaces expose `__all__` for discovery. For a configured client, inspect
`type(ml.rest.documents).post` without issuing a request. Use public imports;
do not copy private implementation details into application code.

[Published API reference](https://monasticus.github.io/mlclient/reference/).

| Namespace | Purpose / when to use |
| --- | --- |
| `mlclient` / `mlclient.clients` | Sync/async clients, manager, reusable connection lifecycle |
| `mlclient.env` | Environment discovery/loading and connection models |
| `mlclient.http` | Generic HTTP, retry/timeout/limits and configuration sentinels |
| `mlclient.auth` / `mlclient.connection` | Auth schemes and transport modes; use configured clients first |
| `mlclient.api` | Named REST/Manage/Admin wrappers; custom API subclasses |
| `mlclient.calls` | Request contracts and reusable custom Calls |
| `mlclient.services` | Eval/documents/CTS orchestration and parsing; stable first choice |
| `mlclient.services.diagnostics` | Logs, log-level and trace events; [investigation workflow](logs.md) |
| `mlclient.functions.xqy` | Pure XQuery builders: cts/fn/xdmp/xs, paths, sequences, namespaces, compilation |
| `mlclient.models` | Documents, metadata, search/value hits, formats and typed configuration |
| `mlclient.responses` / `mlclient.multipart` | MarkLogic error/result parsing and multipart fidelity |
| `mlclient.io` | Document loading/writing and metadata sidecars |
| `mlclient.exceptions` | Classify configuration, transport-facing and server failures |
| `mlclient.logging` | Python logging setup and server forwarding; distinct from server-log reads |
| `mlclient.jobs` | Experimental batch read/write jobs and success/failure reports |

Pure builders compose executable expressions; they do not send requests. Use
`compile()` to obtain code/external variables and `ml.eval.expression()` to
execute. Strings are literal data: use the public `xpath()` helper for paths.
Builder ranges are one-based and inclusive, not Python's slicing semantics.
Check native method signatures instead of inventing argument names.

For jobs inspect `ReadDocumentsJob`/`WriteDocumentsJob` fluent configuration,
`run_sync`/async execution, and reports: a completed batch can contain failed
items. Prefer stable document services unless the job/report workflow is useful.
For models inspect format, metadata categories and serialization contracts;
invalidate cached representations after supported mutable-model edits.
