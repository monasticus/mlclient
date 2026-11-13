# env list

List the environments of the nearest `.mlclient` directory, one name per line.

```sh
ml env list
ml env list --global
```

The command reads the nearest `.mlclient` directory in the current directory or
its parents, and names that directory when it is not the current one. Each
`mlclient-<name>.yaml` file is listed as `<name>`. Inspect one of them with
[`env show`](show.md).

## Options

### `--global`, `-g`

Read `.mlclient` in your home directory instead of searching the project.

See also [global options](../index.md#global-options).
