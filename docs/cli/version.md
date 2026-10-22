# version

![Version demonstration](../assets/gifs/version.gif)

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
`.mlclient/mlclient-dev.yaml`. Repeat the option to select several environments,
for example `-e dev -e test`. Explicit names replace the `local` default;
duplicates run only once, in their first-given order.

Requests run concurrently and results appear in a table with one column per
environment and elapsed times. While running, output is limited to the terminal
height; the final table contains the complete results. A failed environment
returns exit status 1 and does not hide successful peers.

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

See also [global options](index.md#global-options).
