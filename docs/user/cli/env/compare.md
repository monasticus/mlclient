# env compare

Compare settings across environments side by side.

```sh
ml env compare
ml env compare dev-full test-full
ml env compare dev-full test-full --secrets
```

The twin of [`env show`](show.md): it resolves the `.mlclient` directory and
masks secrets the same way, but renders a table whose columns are environments
and whose rows are settings. A value shared by every environment is green even
where a default supplies it; a default that differs from what another
environment set -- the `admin` credentials, a platform app server's port -- is
blue; an explicit value that differs is yellow. A value an environment left to
its default is tagged with an italic `(default)`. Comparison uses the real
values, so two differing passwords read as differing even while both are masked.

A setting left to its default in every environment carries no comparison and is
dropped; pass `--defaults` to keep it. Each app server is rendered in its own
table, matched by id across the environments; a server present in only some
environments leaves the others blank.

## Arguments

### `names`

The environment names to compare, for example `dev-full test-full`. Omit them to
compare every environment in the directory. Naming an environment that does not
exist fails, listing the available names.

## Options

### `--global`, `-g`

Read `.mlclient` in your home directory instead of searching the project.

### `--exclude`, `-e`

Leave an environment out of the comparison. Repeatable, and most useful without
`names`: `ml env compare -e local` compares every environment except `local`.

### `--secrets`, `-s`

Reveal secrets in the table. Without this option, passwords and API keys are
masked, including values inside mappings.

### `--defaults`, `-d`

Keep a setting even when every environment leaves it to the same default, and
render the always-present platform app servers.

See also [global options](../../cli.md#global-options).
