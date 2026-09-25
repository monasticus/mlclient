# url

Print MarkLogic browser URLs for an environment.

```sh
ml url
ml url admin
ml url qc -e dev
ml url monitoring --open
```

URLs are printed in a labelled box. With no target, the QConsole, Admin UI and
Monitoring Dashboard URLs are shown. With a target, that single URL is shown and
the bare URL is copied to the clipboard. With `--open`, the URL is opened in the
default browser instead of being copied.

The known targets are `admin`, `qconsole` (alias `qc`) and the Monitoring
Dashboard (`monitoring`, alias `manage`); each resolves to the matching App
Server's host, port and path in the selected environment. Any other target is
treated as an App Server id and resolves to that server's base URL.

## Arguments

### `target`

The URL to print: `admin`, `qconsole`, `qc`, `manage`, `monitoring`, or an App
Server id. Omit it to print the QConsole, Admin UI and Monitoring Dashboard URLs.

## Options

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

### `--open`

Open the resolved URL in the default browser instead of copying it. Requires a
target.

See also [global options](../cli.md#global-options).
