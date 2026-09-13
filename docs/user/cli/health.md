# health

```text
Description:
  Reports whether a MarkLogic environment's HealthCheck server is up

Usage:
  health [options]

Options:
  -e, --environment=ENVIRONMENT  The ML Client environment name [default: "local"]
  -w, --watch                    Poll until interrupted instead of checking once
  -i, --interval=INTERVAL        Seconds between polls in --watch mode [default: "5"]
  -o, --overwrite                Repaint poll output in place instead of scrolling
  -l, --lines=LINES              Statuses to keep on screen in --overwrite mode [default: "3"]
  -h, --help                     Display help for the given command. When no command is given display help for the list command.
  -q, --quiet                    Do not output any message.
  -V, --version                  Display this application version.
      --ansi                     Force ANSI output.
      --no-ansi                  Disable ANSI output.
  -n, --no-interaction           Do not ask any interactive question.
  -v|vv|vvv, --verbose           Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.
```

The command sends a `HEAD /` request to the environment's HealthCheck server (see [setup](../setup.md) ) and prints a coloured status:

- `HEALTHY` (green) when the server answers with a success code,
- `UNHEALTHY` (red) when it answers with a failure code.

The command uses the environment's `health` configuration directly; no REST server is required. A single check exits with `0` for `HEALTHY` and `1` for `UNHEALTHY`.

## Check once

```bash
ml health -e local
```

## Watch until interrupted

Pass `--watch` (`-w`) to keep polling until you interrupt with Ctrl-C. Each status is printed on its own line, prefixed with the local timestamp. When the server cannot be reached or a request times out, `UNREACHABLE` (yellow) is printed and polling continues. Subsequent successful requests show the current health status. Ctrl-C stops polling cleanly:

```bash
ml health -e local --watch
```

`--interval` (`-i`) sets the seconds between polls (default `5`, between `1` and `3600`):

```bash
ml health -e local --watch --interval 10
```

## Repaint in place

In watch mode, `--overwrite` (`-o`) repaints the output in place instead of scrolling the terminal, keeping the last `--lines` (`-l`) statuses visible (default `3`, between `1` and `100`):

```bash
ml health -e local --watch --overwrite --lines 5
```

With `--no-ansi`, statuses are appended normally instead of repainting. Redirected output behaves the same way unless ANSI is explicitly enabled.

Without `--watch` the `--interval`, `--overwrite` and `--lines` options are ignored.
