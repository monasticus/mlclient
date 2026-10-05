# Investigate logs across a cluster

## Choose the question first

| Question | Start with | Correlate with |
| --- | --- | --- |
| Did the incident affect one node or the cluster? | All-host error logs in a narrow interval | Host/forest status, deployment/restart times |
| Why did a request fail? | Error events and full multiline messages | Access/request logs for the same App Server and interval |
| Which endpoint or client is involved? | App Server access logs | Request details where request logging is enabled |
| Is indexing, merging or recovery involved? | Error log messages | Database/forest status and meters; logs alone do not measure completion |
| Was access denied or security changed? | Error and available audit logs | Configured auditing policy, user/role privileges |
| Did an async script time out? | Client exception and matching server events | Connect/read/write/pool timeout, retries and operation deadline |

Use actual incident times. Begin with a small time window across all hosts,
then narrow by hostname, App Server and regex. A regex can hide preceding
warnings and related events: retain an unfiltered interval around a matching
failure. Preserve multiline messages and stack frames; count events, not lines.

## CLI: fastest cluster investigation

```sh
ml logs -e dev --all-hosts --from '2026-10-05T10:00:00' --to '2026-10-05T10:05:00'
ml logs -e dev --all-hosts --from '2026-10-05T10:00:00' --regex 'XDMP-|SVC-'
ml logs -e dev --all-hosts -s content --from '2026-10-05T10:00:00'
ml logs -e dev -H host-1 --list
ml logs -e dev -H host-1 -s content -l access
ml logs -e dev -H host-1 -s content -l request
ml logs -e dev -s TaskServer --from '2026-10-05T10:00:00'
```

Replace `content` with an environment App Server identifier or its numeric port.
No `-s` selects `ErrorLog.txt`; `-s 0`/`TaskServer` selects Task Server logs.
`--all-hosts` discovers cluster hosts through Manage, reads concurrently and
merges error events chronologically with host labels. It supports Manage-only
environments. It cannot combine with `--host`, `--list` or non-error log types.
A failed host read fails the command; do not describe the output as complete
when the command failed. This is a snapshot, not a follow/tail subscription.

The single-host CLI currently obtains the environment's default REST client
and uses its Manage API connection; a Manage-only configuration should use
`--all-hosts` or an explicitly selected Manage client in Python.

Time/regex filters apply to **error** logs only. Access/request/audit records
are returned as text lines, without the error service's structured timestamp
and level. Logging/auditing must be enabled to have useful records; absence of
records does not prove absence of activity.

**Time zones:** the current LogsCall converts filters to second-resolution
`YYYY-MM-DDTHH:MM:SS`, dropping offsets and fractions. Convert incident times to
the server's wall-clock timezone first. Do not assume passing `Z` or `+02:00`
preserves that offset. Investigate clock skew before inferring causality from
cluster ordering; thread/request identifiers need the host context.

## Python: structured reports and custom selection

```python
from mlclient import MLClientManager
from mlclient.services.diagnostics import AsyncLogsService

async def incident(host, start, end):
    async with MLClientManager('dev').get_async_client('manage') as ml:
        service = AsyncLogsService(ml.manage)
        files = await service.list(host=host)
        entries = await service.get(
            host=host, start_time=start, end_time=end, timeout=30,
        )
        return files, [{**event, 'host': host} for event in entries]
```

`await get()` returns a **normal iterator**: iterate with `for`, not `async for`.
Error events contain `timestamp`, `level`, `message`; non-error events contain
`message`. Sync `LogsService` has the same selection and output contracts without
`await`. `list()` supplies `source`, `parsed` and `grouped` views of available
files. Inspect those files per host before drawing conclusions about coverage.

For custom multi-host reports, discover hosts with
`await ml.manage.hosts.get_list(data_format='json')`, check status, then read
`host-default-list.list-items.list-item[*].nameref`. Reuse one async client;
fetch in bounded batches with `asyncio.gather`, tag each event with its host,
and cancel/await siblings on failure before closing the client. Use the
[concurrency template](templates.md) for that lifecycle. Preserve failures in
any deliberately partial report, together with hosts/files/time scope.

## Rotations and raw contracts

High-level `get()` and CLI read the selected **current file**. They do not
search every rotation. List files, select rotations intersecting the incident,
and fetch them explicitly:

```python
response = await ml.manage.logs.get(
    filename='ErrorLog_1.txt', host='host-1', data_format='json',
    start_time=start, end_time=end,
)
response.raise_for_status()
payload = response.json()
```

Use the filename actually returned by listing. A numeric rotation suffix does
not establish the calendar date of its contents. Different hosts can rotate at
different times. The wrapper accepts XML/JSON/HTML formats; use raw HTTP only
when the matching server contract needs an unsupported option. Consult
[endpoint contracts](endpoints.md) for `/manage/v2/logs` and response shapes;
do not assume a rotated file has the same structured response as current logs.

## Temporary diagnostics and reporting

`ml log-level` and `ml trace-events` have dedicated synchronous services
`LogLevelService` and `TraceEventsService`. Read current settings, enable only
the requested diagnostics, and restore original values afterwards. Trace
volume can change workload behaviour. Do not invent async service equivalents.

A useful report states environment, hosts, files/rotations, timezone and interval,
then gives a short chronology with host, severity, error code and full relevant
message. Separate evidence from hypotheses and missing coverage. Remove
credentials/tokens and sensitive document content before sharing logs.
Python `mlclient.logging` configures client logging and can forward Python
records to MarkLogic via `MLLogHandler`; it is separate from reading server
logs. See the [API selection and inspection](api-coverage.md) for handler lifecycle.
