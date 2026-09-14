# health

Check whether the environment's HealthCheck server is healthy.

```sh
ml health
```

Keep checking until Ctrl-C, including while the server is unreachable:

```sh
ml health --watch
ml health --watch --interval 10 --overwrite --lines 5
```

The command uses the environment's `health` connection and sends `HEAD /`;
it does not require a REST App Server.

## Options

### `--watch`, `-w`

Poll until interrupted with Ctrl-C. Each status includes a local timestamp.
Connection errors and timeouts print `UNREACHABLE`; polling continues and shows
recovery on a later successful request.

### `--interval`, `-i`

Seconds between polls. Default: `5`; allowed range: `1`–`3600`.
Ignored without `--watch`.

### `--overwrite`, `-o`

Repaint recent statuses in place instead of scrolling. Requires `--watch`.
With `--no-ansi`, or redirected output without forced ANSI, statuses are appended
normally instead of repainting.

### `--lines`, `-l`

Number of statuses retained by `--overwrite`. Default: `3`; allowed range:
`1`–`100`. Ignored without `--watch`.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

## Status and exit codes

| Status | Meaning |
| --- | --- |
| `HEALTHY` | HealthCheck returned a success response |
| `UNHEALTHY` | HealthCheck returned a failure response |
| `UNREACHABLE` | A watch-mode probe could not connect or timed out |

A single check exits with `0` for healthy and `1` for unhealthy. A connection error
outside watch mode is reported as an error. Watch mode continues through failures
until interrupted.

See also [global options](../cli.md#global-options).
