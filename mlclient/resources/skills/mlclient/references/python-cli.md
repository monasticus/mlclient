# CLI and Python execution

## Evaluation

```sh
ml eval -e dev -c content -x '1 + 1'
ml eval -e dev -c content -j '1 + 1'
ml eval -e dev -c content ./query.xqy -d Documents
ml eval -e dev -c content ./query.js
ml eval -e dev -x 'declare variable $uri external; fn:doc($uri)' --var uri=/a.json
ml eval ./query.xqy --no-pretty
```

Eval/sample pretty-print XML/JSON by default. Use `--no-pretty` for pipelines.
HTTP prints the original response; opt into `--pretty`. Inline `-j` means
JavaScript on eval, JSON on sample. CLI external variables are strings: cast in
XQuery where needed. Use `{namespace-uri}local-name` keys for namespaced bindings.

```python
from mlclient import MLClientManager

with MLClientManager('dev').get_client('content') as ml:
    values = ml.eval.file(
        'query.xqy', variables={'uri': '/a.json'},
        database='Documents', timeout=10,
    )
    other = ml.eval.file('query.sjs')

```

Services parse XML/JSON/scalars and eval can return a scalar or a sequence.
Do not assume every result is a list. Use supported `output_type` when a known
shape needs conversion. The file extension chooses the language. Python strings
are local code; `file()` sends the file contents, not a server-side module path.
External XQuery declarations must exist in raw code; the service does not insert
them. The expression builder manages its own generated bindings.

## Raw requests

```sh
ml http get /v1/documents uri=/a.json 'Accept:application/json' -e dev
ml http get /manage/v2/databases format=json -c manage -e dev --pretty
ml http post /v1/search 'Content-Type:application/json' --body @query.json -e dev
```

Check `ml http --help` for body-file syntax in the installed version. `key=value`
adds a query parameter; `key:value` a header. Repeat query tokens for multi-values.
Do not concatenate query values into URL paths. A path alone never changes ports.

```python
from mlclient import MLClientManager

with MLClientManager('dev').get_client('content') as ml:
    response = ml.http.get('/v1/search', params={'q': 'coffee', 'pageLength': 10})
    response.raise_for_status()
    result = response.json()
```

MLClient raw HTTP uses `body=`, not httpx's `json=` keyword. A dict body becomes
JSON only with an application/json Content-Type; otherwise it is form data.
Use explicit headers for generic POST/PUT. Named wrapper bodies already use
their endpoint's content-type rules. Parse MarkLogic-specific error bodies with
`ml.parser.raise_for_status(response)` where useful, then `.parse(response)`.
Dedicated services handle status and parsing themselves.

## Async: fewer requests first, then concurrency

Use bulk document calls and one server-side aggregate before creating N requests.
Choose sync for a small sequential script; choose async for independent network
operations and applications already running an event loop. It reduces waiting,
not server execution cost. Keep dependent reads/writes ordered.

```python
import asyncio
from mlclient import MLClientManager

async def inspect():
    async with MLClientManager('dev').get_async_client('content') as ml:
        health, version, response = await asyncio.gather(
            ml.healthcheck(), ml.version(),
            ml.manage.databases.get_list(data_format='json'),
        )
        response.raise_for_status()
        return health, version, response.json()

# At a script entry point; await inspect() in an existing loop instead.
if __name__ == '__main__':
    print(asyncio.run(inspect()))
```

For a large workload, copy [bounded evaluation](../assets/concurrent_eval.py).
`gather` propagates failures without automatically cancelling all siblings.
Cancel and await remaining tasks before client closure, or use TaskGroup on
Python 3.11+. Do not swallow cancellation. Avoid calling synchronous MLClient
inside async request handlers; use AsyncMLClient. For sync-only diagnostics,
use an explicit worker thread if needed, owning the sync client in that thread.

Docs: [eval](https://monasticus.github.io/mlclient/user/python/eval/),
[async](https://monasticus.github.io/mlclient/user/python/async/),
[CLI HTTP](https://monasticus.github.io/mlclient/user/cli/http/).
