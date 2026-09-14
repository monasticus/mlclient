# log-level

Show or change a group or App Server log level.

```sh
ml log-level
ml log-level debug
```

The command shows the group file log level by default. Reading or setting a level
prints the same output format:

```text
Group: Default
File Log Level: info
```

Target a group's system log level or an App Server's file log level:

```sh
ml log-level -t system -g Default
ml log-level -s App-Services
ml log-level warning -s App-Services
```

## Arguments

### `level`

Optional new log level. Omit it to read the current value. Supported values:
`finest`, `finer`, `fine`, `debug`, `config`, `info`, `notice`, `warning`, `error`,
`critical`, `alert`, `emergency`.

## Options

### `--type`, `-t`

Log type: `file` (default) or `system`. App Servers support only `file`.

### `--group`, `-g`

MarkLogic group name. Defaults to `Default`.

### `--server`, `-s`

Actual MarkLogic App Server name, such as `App-Services`. This is the target of
the operation, not a connection identifier or port. Omit it to act on the group.
May only be combined with `--type file`.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings. For example, `-c content` selects a named connection and
`-c 8100` uses port 8100.

## Permissions and diagnostics

The command first evaluates Admin module functions through the selected REST
connection. Only authorization failures trigger Management REST fallback.
Reading App Server properties through that fallback requires `manage-user`;
reading group properties or changing either target requires `manage-admin`
(or equivalent privileges).

If both paths refuse access, the error names the required Management role.
Transport and other server errors retain their original meaning and do not
trigger a Management retry.

Use `ml log-level -vv` to see the eval attempt, any authorization failure,
and the Manage fallback result. There is no separate Admin REST fallback.

See also [global options](../cli.md#global-options).
