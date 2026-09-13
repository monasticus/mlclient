# Command line guide

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

## Run everyday commands

```sh
ml eval -x '1 + 1'
ml http get /v1/documents uri=/example.json
ml logs -s 8002
ml log-level
ml health
ml version -c app-services
```

The `local` environment is the default. Use `-e dev` for another environment.
A connection selector chooses where the request is sent; an operation target
chooses what the server acts on. The distinction is explained below and on each
command page.

## Command reference

```text
MLCLIent (version 0.4.0)

Usage:
  command [options] [arguments]

Options:
  -h, --help            Display help for the given command. When no command is given display help for the list command.
  -q, --quiet           Do not output any message.
  -V, --version         Display this application version.
      --ansi            Force ANSI output.
      --no-ansi         Disable ANSI output.
  -n, --no-interaction  Do not ask any interactive question.
  -v|vv|vvv, --verbose  Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.

Available commands:
  eval       Sends a POST request to the /v1/eval endpoint
  health     Reports whether a MarkLogic environment's HealthCheck server is up
  help       Displays help for a command.
  http       Sends a raw HTTP request to any REST endpoint
  list       Lists commands.
  log-level  Shows or sets a MarkLogic file/system log level
  logs       Sends a GET request to the /manage/v2/logs endpoint
  version    Reports the MarkLogic version of an environment

 env
  env init   Scaffolds an MLClient environment configuration file
  env show   Lists MLClient environments, or renders one environment's settings
```

The former `call eval` and `call logs` commands are now `eval` and `logs`. Use `http` for raw requests to other REST endpoints.

## Connection and target selection

`http`, `eval`, `version` and `log-level` use `-c / --connection` to select a configured connection identifier or a TCP port. A numeric port changes the default REST connection's port and retains its other settings.

`logs -s / --server` selects whose logs to read by an environment identifier or port. `log-level -s / --server` instead takes the actual App Server name in MarkLogic. It does not select the connection used for the request.

Server commands default to the `local` environment; `-e / --environment` selects another environment. These connection options replace the former `-s / --rest-server`; `logs --server` replaces `--app-server`.

!!! caution
    All MLClient commands use MLClient Environment. To set it up, see [setup](./setup.md) .

Log-level diagnostics are available with `ml log-level -vv`. Debug messages show the eval attempt (which runs the Admin module), authorization failures that trigger Manage REST fallback, and the result or reason for failure. There is no separate Admin REST fallback.
