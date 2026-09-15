# logs

Read MarkLogic log entries or list available log files.

```sh
ml logs
ml logs -s 8002
ml logs --list
```

The first command reads the main `ErrorLog.txt`; `-s 8002` selects
`8002_ErrorLog.txt`. Narrow an error log by time or regular expression:

```sh
ml logs -s 8002 --from 10:00 --to 12:00
ml logs -s 8002 --regex 'Forest M.*'
```

## Options

### `--server`, `-s`

App Server identifier from the environment or its port. Identifiers resolve to
the configured port; unknown identifiers are rejected. `TaskServer` and `0` both
select Task Server logs. With no selector, read the main server log.

This selects whose logs to read, not the connection used for the request.

```sh
ml logs -s app-services
ml logs -s TaskServer
```

### `--log-type`, `-l`

Log type: `error` (default), `access` or `request`.

```sh
ml logs -s 8002 --log-type access
```

### `--from`, `-f`

Start time for error-log filtering. Accepts a time, date or date and time.
Quote values containing spaces.

```sh
ml logs --from '2026-09-01 10:00'
```

### `--to`, `-t`

End time for error-log filtering, in the same forms as `--from`.

```sh
ml logs --from 2026-09-01 --to 2026-09-03
```

### `--regex`, `-r`

Regular expression used to filter error logs. Quote the expression to keep the
shell from interpreting it. `--from`, `--to` and `--regex` apply only to error logs.

### `--host`, `-H`

MarkLogic host from which to retrieve log data. This selects a host within the
server operation; it does not replace the environment's connection hostname.

### `--all-hosts`

Read error logs from every host in the cluster at once, merged into a single
timeline by timestamp. The host is shown in parentheses between the log level
and the message. The host list comes from `/manage/v2/hosts`, and each host is
queried concurrently. If host discovery or any host read fails, the command
fails without printing a partial timeline. Error logs only: `--all-hosts` with
any other log type is rejected. `--all-hosts` cannot be combined with `--host` or `--list`.

Reading unfiltered error logs from every host can return a large volume and may
time out, so a multi-host read with no `--from`, `--to` or `--regex` prints a
warning suggesting you narrow it.

```sh
ml logs -e dev --all-hosts
ml logs -e dev --all-hosts --from '2026-09-01 10:00' --regex 'Forest M.*'
```

### `--list`

List available log files instead of reading entries. Combine with `--server`
or `--host` to narrow the list.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

See also [global options](../cli.md#global-options).
