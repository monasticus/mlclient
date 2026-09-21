# env compare

Compare settings across environments side by side.

```sh
ml env compare
ml env compare dev-full test-full
ml env compare dev-full test-full --secrets
```

The twin of [`env show`](show.md): it resolves the `.mlclient` directory and
masks secrets the same way, but renders a table whose columns are environments
and whose rows are settings. Each cell holds the environment's effective value,
so a setting an environment leaves to its default -- the `admin` credentials,
the always-present platform app servers -- still appears, shown blue to flag
that the environment did not set it. An explicit value identical across every
environment is green; an explicit value that differs is yellow. Comparison uses
the real values, so two differing passwords read as differing even while both
are masked.

Each app server is rendered in its own table, matched by id across the
environments; a server present in only some environments leaves the others
blank.

## Arguments

### `names`

The environment names to compare, for example `dev-full test-full`. Omit them to
compare every environment in the directory. Naming an environment that does not
exist fails, listing the available names.

## Options

### `--global`, `-g`

Read `.mlclient` in your home directory instead of searching the project.

### `--secrets`, `-s`

Reveal secrets in the table. Without this option, passwords and API keys are
masked, including values inside mappings.

See also [global options](../../cli.md#global-options).
