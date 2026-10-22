# health

![Health demonstration](../assets/gifs/health.gif)

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

Check every host of the cluster instead:

```sh
ml health --cluster
ml health --cluster -v
ml health --cluster --watch
```

## Cluster health

With `--cluster` the environment's first REST App Server evaluates a query that
probes the HealthCheck server of every host from inside the cluster, so hosts
with internal names are checked too. The status is followed by the number of
healthy hosts out of all:

```text
UNHEALTHY 10/12
  UNHEALTHY  ip-10-0-0-14.ec2.internal
  UNHEALTHY  ip-10-0-0-91.ec2.internal
```

Unhealthy hosts are listed below the status, sorted by name with the numbers in
names ordered by value; `-v` lists every host in the same order. In watch mode the
unhealthy hosts follow the status on its line
(`UNHEALTHY 11/12 down: ip-10-0-0-14.ec2.internal`). In a table
of several environments, only the status and the host count are shown.

The query needs the eval privilege. Without it, on MarkLogic 11 or later, the
Management API health check is read instead: it gives a verdict for the whole
cluster without per-host health, shown as `HEALTHY (overall)` or
`UNHEALTHY (overall)`. Each host has two seconds to answer, and hosts are probed
one after another.

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

### `--cluster`, `-c`

Check every host of the cluster instead of the HealthCheck server the `health`
connection reaches. Requires a REST App Server in the environment. See
[Cluster health](#cluster-health).

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`. Repeat the option to select several environments,
for example `-e dev -e test`. Explicit names replace the `local` default;
duplicates run only once, in their first-given order.

## Status and exit codes

| Status | Meaning |
| --- | --- |
| `HEALTHY` | HealthCheck returned a success response |
| `UNHEALTHY` | HealthCheck returned a failure response |
| `UNREACHABLE` | A watch-mode probe could not connect or timed out |
| `HEALTHY 12/12` | With `--cluster`: every host is healthy |
| `UNHEALTHY 10/12` | With `--cluster`: some hosts are unhealthy |
| `HEALTHY (overall)` | With `--cluster`, without the eval privilege: the cluster reports itself healthy |

A single check exits with `0` for healthy and `1` for unhealthy. A connection error
outside watch mode is reported as an error. Watch mode continues through failures
until interrupted.

See also [global options](index.md#global-options).
