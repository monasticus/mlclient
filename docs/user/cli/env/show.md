# env show

List environments, inspect their settings or copy one value.

```sh
ml env show
ml env show local
ml env show local host
```

The command reads the nearest `.mlclient` directory in the current directory or
its parents. Values come from the configuration file. Secrets are masked in the
formatted output unless `--secrets` is passed.

## Arguments

### `name`

Environment name. Omit it to list available names, one per line. For example,
`local` selects `mlclient-local.yaml`.

### `setting`

Optional root setting or App Server identifier. A root setting prints its value;
an App Server renders a table of that server's settings.

```sh
ml env show local host
ml env show local app-services
```

Predefined servers (`app-services`, `manage`, `admin`, `health`) can be inspected
even when the file does not list them; in that case their defaults are shown.

## Options

### `--global`, `-g`

Read `.mlclient` in your home directory instead of searching the project.

### `--raw`

Print the configuration file verbatim, including secret values. No formatting,
masking or YAML validation is applied.

```sh
ml env show local --raw
```

### `--secrets`, `-s`

Reveal secrets in formatted output. Without this option, passwords, OAuth tokens,
API keys and TLS key passwords are masked, including values inside mappings and
lists.

### `--defaults`, `-d`

Fill in root defaults and resolve server inheritance, including default ports,
fieldwise SSL settings and the always-present platform app servers. Explicit
`auth: null` and `auth: app` display as `app`.

```sh
ml env show local content --defaults
```

This inspects configuration without connecting, loading certificate files or
requiring Kerberos tooling. Transport/authentication compatibility is validated
when creating a client. Without `--defaults`, the command keeps showing the raw
fields, including incomplete configurations and unknown keys.

### `--copy`, `-c`

Copy a simple setting while also printing it:

```sh
ml env show local host --copy
ml env show local password -c
```

Text, numbers and booleans are supported. The clipboard receives the original
value, **including an unmasked password even without `--secrets`**. Terminal
output remains masked. A successful copy is followed by *Copied to clipboard.*
in green. Copied text has no formatting or trailing newline; booleans use
`true` or `false`.

For a whole environment, environment list, mapping, list, null, App Server table
or `--raw` output, the command displays the result and then warns that copying
was skipped. A missing clipboard utility or session also produces a warning
without failing the command.

Clipboard support uses `xclip` on Linux/X11, `wl-copy` on Wayland, `pbcopy` on
macOS or `clip` on Windows.

See also [global options](../../cli.md#global-options).

## Invalid configuration

An empty file renders as an empty environment. Otherwise, YAML must contain a
mapping. `app-servers` may be omitted, null or a list of mappings with non-empty
`id` values. Errors name the file without printing its contents.

With `--defaults`, empty or null YAML uses the environment defaults, and null
`app-servers` is treated as an empty list. Typed fields are validated; errors
identify their locations without printing input values, including at `-vvv`.
