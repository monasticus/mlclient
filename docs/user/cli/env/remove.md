# env remove

Delete an environment configuration file.

```sh
ml env remove dev
ml env remove dev --force
```

The command resolves `mlclient-<name>.yaml` the same way [`env show`](show.md)
does: it reads the nearest `.mlclient` directory in the current directory or its
parents, or the home directory with `--global`. It asks for confirmation before
deleting; answering no leaves the file untouched.

## Arguments

### `name`

Environment name. For example, `dev` selects `mlclient-dev.yaml`. The command
fails if the file does not exist, listing the available names.

## Options

### `--global`, `-g`

Remove the file in the `.mlclient` directory in your home directory instead of
searching the project.

### `--force`, `-f`

Delete without asking for confirmation. A non-interactive invocation never
confirms, so `--force` is required to remove a file from a script.

See also [global options](../../cli.md#global-options).
