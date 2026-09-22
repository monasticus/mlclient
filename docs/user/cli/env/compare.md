# env compare

Compare settings across environments side by side.

```sh
ml env compare
ml env compare dev staging
ml env compare dev staging --secrets
```

The twin of [`env show`](show.md): it resolves the `.mlclient` directory and
masks secrets the same way, but renders a table whose columns are environments
and whose rows are settings. A value shared by every environment is green even
where a default supplies it; a default that differs from what another
environment set -- the `admin` credentials, a platform app server's port -- is
blue; an explicit value that differs is yellow. A value an environment left to
its default is tagged with an italic `(default)`. Comparison uses the real
values, so two differing passwords read as differing even while both are masked.

Server settings include inherited root values, default ports and fieldwise SSL
overrides. Explicit `auth: null` and `auth: app` both display as `app`. A
`(default)` label means the value was not written at that level: it can come from
the root configuration or a built-in default.

Equal settings left to defaults in every environment are omitted; pass
`--defaults` to keep them. Differing inherited values remain visible. Each app
server has its own table, matched by id; missing servers display dashes.

## Arguments

### `names`

The environment names to compare, for example `dev staging`. Omit them to
compare every environment in the directory. Naming an environment that does not
exist fails, listing the available names.

## Options

### `--global`, `-g`

Read `.mlclient` in your home directory instead of searching the project.

### `--exclude`, `-e`

Leave an environment out of the comparison. Repeatable, and most useful without
`names`: `ml env compare -e local` compares every environment except `local`.

### `--secrets`, `-s`

Reveal secrets in the table. Without this option, passwords, OAuth tokens, API
keys and TLS key passwords are masked, including values inside mappings.

### `--defaults`, `-d`

Keep a setting even when every environment leaves it to the same default, and
render the always-present platform app servers.

See also [global options](../../cli.md#global-options).

## Configuration validation

Empty or null YAML uses the environment defaults; null `app-servers` is treated
as an empty list. Invalid YAML or typed fields produce an error naming the file
and, for typed fields, the field location without exposing input values.

Comparison does not connect to MarkLogic, load certificate files or require
Kerberos tooling. It compares inherited configuration before validating whether
the transport and authentication combination can create a client. Without ANSI
colors, masked differing secrets both appear as `****`.
