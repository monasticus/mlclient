# Administration and monitoring

## Pick the tier

| Operation | Default tier | Preferred path |
| --- | --- | --- |
| Content/eval/queries | REST: 8000 or custom | documents/eval/CTS services |
| Hosts/forests/databases/security/logs | Manage: 8002 | `ml.manage.*` |
| Bootstrap/config for cluster join | Admin: 8001 | `ml.admin.*` / explicit raw Admin client |
| Health | Health: 7997 | `ml.healthcheck()` |

Actual configurations can change host/port/auth per tier. Reading a path never
switches `.http` automatically. Manage/Admin-only operations can use
`manager.get_client('manage')` or `'admin'` even without a configured REST server.

```python
from mlclient import MLClientManager

with MLClientManager('dev').get_client('manage') as ml:
    response = ml.manage.databases.get('Documents', view='status', data_format='json')
    response.raise_for_status()
    status = response.json()
    healthy = ml.healthcheck()
    version = ml.version
```

Async equivalents await request methods, `healthcheck()` and `version()`.
Health false is a probe result; auth/config/transport errors can raise. Wrap a
polling coroutine in an overall deadline and bound every probe. A fast probe is
not evidence that every forest, replica or application function is ready.

## Logs

Start with [cluster log investigation](logs.md): `ml logs --all-hosts` for a
chronological cluster error-log view; services for structured reports; named
Manage calls for explicit rotations. That guide covers timezones, non-error
log formats, missing coverage and temporary diagnostic settings.

## Configuration changes

Read current properties via `.get_properties(..., data_format='json')`.
Create a narrow desired change and inspect its diff. Named `.put_properties`
accepts dict JSON or XML/string according to endpoint rules. Verify what fields
are merged/replaced and allowed for that server version before sending a full
object. Status and metrics documents are not configuration payloads.

Use raw HTTP for unwrapped endpoints. Escape resource names in path segments
and pass query values separately. Management includes users/roles/privileges,
forests, databases, hosts, groups, servers, meters and many additional families;
see the complete [endpoint navigator](endpoints.md).

Some accepted changes trigger restarts/reindexing. Inspect response status and
restart timestamp where provided; use `ml.wait_for_restart(response, timeout=...)`
(or awaited equivalent) only when a restart is expected. Confirm both the change
and resulting health/status, and inspect logs on failure. For index changes,
check database reindex progress rather than treating HTTP 200 as completion.

Use the existing authentication configuration; do not assume every deployment
requires digest (basic, certificates, OAuth and Cloud also exist). Distinguish
missing privilege, network failure, wrong tier/URL, and unavailable index before
changing credentials or settings. Avoid disabling TLS or elevating privileges as
an automatic fallback.

Docs: [health/admin](https://monasticus.github.io/mlclient/user/python/health-and-administration/).
