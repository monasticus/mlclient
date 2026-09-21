# env compare

Compare settings across environments side by side.

```sh
ml env compare
ml env compare dev-full test-full
ml env compare dev-full test-full --secrets
```

The twin of [`env show`](show.md): it resolves the `.mlclient` directory and
masks secrets the same way, but renders a table whose columns are environments
and whose rows are settings. A value identical across every environment is
green; a value that differs, or that is missing from some environment, is
yellow. Comparison uses the real values, so two differing passwords read as
differing even while both are masked.

Each app server is rendered in its own table, matched by id across the
environments; a server missing from an environment leaves that column blank.

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
