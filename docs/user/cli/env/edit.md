# env edit

Open an environment configuration file in your own editor.

```sh
ml env edit local
ml env edit dev --global
```

The command resolves `mlclient-<name>.yaml` the same way [`env show`](show.md)
does: it reads the nearest `.mlclient` directory in the current directory or its
parents, or the home directory with `--global`. It then launches the editor and
returns when the editor exits, forwarding the editor's exit status.

The editor is taken from `$VISUAL`, then `$EDITOR`, falling back to `vi` when
neither is set. The editor inherits the terminal, so full-screen editors work as
usual.

## Arguments

### `name`

Environment name. For example, `local` selects `mlclient-local.yaml`. The
command fails if the named file does not exist, listing the available names.

## Options

### `--global`, `-g`

Edit the file in the `.mlclient` directory in your home directory instead of
searching the project.

See also [global options](../../cli.md#global-options).
