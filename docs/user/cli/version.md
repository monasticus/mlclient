# version

Print the complete MarkLogic Server version.

```sh
ml version
ml version -e dev
ml version -c content
```

For example, output may be `12.0.1` or `10.0-9.5`. All numeric components,
separators and suffixes are preserved. To print the **MLClient package version**,
use the global `ml --version` option instead.

## Options

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings. For example, `-c content` selects a named connection and
`-c 8100` uses port 8100.

## Version lookup

The command evaluates `xdmp:version()` on the selected REST server. If the user
lacks the eval privilege, it tries Manage and then Admin endpoints. Unavailable
endpoints and malformed fallback responses are skipped. If none succeeds, the
original eval error is reported. An invalid eval version also makes the command
fail; a connection error does not trigger an auxiliary-server fallback.

See also [global options](../cli.md#global-options).
