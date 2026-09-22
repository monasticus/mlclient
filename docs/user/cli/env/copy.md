# env copy

Clone an environment configuration under a new name.

```sh
ml env copy prod prod-test
ml env copy prod prod-test --edit
```

The command resolves the source the same way [`env show`](show.md) does: it
reads the nearest `.mlclient` directory in the current directory or its parents,
or the home directory with `--global`. It writes the source file verbatim -
comments included - to `mlclient-<target>.yaml` beside it, then leaves both files
in place for you to tweak the copy.

Copying preserves bytes, including line endings, and source file permissions.
When replacing a target, permissions are restricted to those allowed by both
files. The completed copy is published atomically; a failed copy leaves an
existing target unchanged. `--force` replaces a target symlink itself rather
than writing through it.

## Arguments

### `source`

Environment name to copy from. The command fails if the file does not exist,
listing the available names.

### `target`

Environment name to copy to. Written next to the source. The command refuses to
overwrite an existing target unless `--force` is given.

## Options

### `--global`, `-g`

Copy within the `.mlclient` directory in your home directory instead of
searching the project.

### `--force`, `-f`

Overwrite the target file when it already exists.

### `--edit`, `-e`

Open the copy in your editor after copying, as if by [`env edit`](edit.md). The
editor is taken from `$VISUAL`, then `$EDITOR`, falling back to `vi`.

```sh
ml env copy prod prod-test --edit
```

See also [global options](../../cli.md#global-options).
