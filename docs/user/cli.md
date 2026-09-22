# Command line interface

Use `ml` to inspect an environment, evaluate code, work with logs or send a raw
HTTP request. Every command has `--help`; use `-vv` for diagnostic logs.

## Connect a project

For a new project, run `ml env init` and review the generated connection settings.
For an ml-gradle project, import the properties already present:

```sh
ml env init --from-gradle=dev
ml version -e dev
```

This merges `gradle.properties` and `gradle-dev.properties`. It reads configuration;
it does not run Gradle or deploy the project.

For a running server, discovery can populate connections from its App Servers:

```sh
ml env init local --from-host=localhost:8002 --interactive
ml env show local
```

Supply the host's credentials when prompted. Discovery uses the Manage API and
needs permission to read server configuration. One environment can contain many
App Server entries; review the discovered identifiers before using them.
See [env init](cli/env/init.md) for discovery filters and configuration details.

Manage the configuration files with the [env commands](cli/env.md):

```sh
ml env copy local dev
ml env edit dev
ml env compare local dev
ml env remove dev
```

These commands work on local files; they do not deploy or change a MarkLogic
server. Removal asks for confirmation.

## Run everyday commands

```sh
ml eval -x '"Hello World!"'
ml http get /v1/documents uri=/example.json
ml logs -s 8002
ml log-level
ml health
ml version
```

The `local` environment is the default. Use `-e dev` for another environment.
A connection selector chooses where the request is sent; an operation target
chooses what the server acts on. The distinction is explained below and on each
command page.

## Find a command

| Task | Command |
| --- | --- |
| Create or inspect project configuration | [`ml env`](cli/env.md), with [`init`](cli/env/init.md) and [`show`](cli/env/show.md) |
| Run XQuery or JavaScript | [`ml eval`](cli/eval.md) |
| Send an HTTP request | [`ml http`](cli/http.md) |
| Read server logs | [`ml logs`](cli/logs.md) |
| Inspect or change a log level | [`ml log-level`](cli/log-level.md) |
| Inspect or change diagnostic trace events | [`ml trace-events`](cli/trace-events.md) |
| Check server health, once or continuously | [`ml health`](cli/health.md) |
| Read the MarkLogic version | [`ml version`](cli/version.md) |

Use `ml --help` for global options and `ml env init --help` (or another command)
for its arguments. The pages above explain workflows, defaults and examples.

## Connection and target selection

`http`, `eval`, `version`, `log-level` and `trace-events` use `-c / --connection` to select a configured connection identifier or a TCP port. A numeric port changes the default REST connection's port and retains its other settings.

`logs -s / --server` selects whose logs to read by an environment identifier or port. `log-level -s / --server` instead takes the actual App Server name in MarkLogic. It does not select the connection used for the request.

Server commands default to the `local` environment; `-e / --environment` selects another environment.


## Global options

These options apply to every command. Command-specific flags are described on
the corresponding command page.

### `--help`, `-h`

Display help for a command, for example `ml env init --help`.

### `--version`, `-V`

Print the MLClient package version. Use [`ml version`](cli/version.md) for the
MarkLogic Server version.

### `--quiet`, `-q`

Suppress command output.

### `--verbose`, `-v`

Increase verbosity; repeat as `-vv` or `-vvv` for more detail.

### `--ansi` and `--no-ansi`

Force or disable terminal styling. Disabling ANSI also prevents in-place
repainting in [`ml health`](cli/health.md).

### `--no-interaction`, `-n`

Do not prompt for input. Supply the required values explicitly when scripting.
