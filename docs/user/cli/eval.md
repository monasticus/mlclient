# eval

Run XQuery or server-side JavaScript and print the result.

```sh
ml eval -x '"Hello World!"'
ml eval -j '"Hello World!"'
ml eval ./query.xqy
```

Use `-d` to select a content database, or pass external variables with `--var`:

```sh
ml eval ./query.xqy -d Documents
ml eval -x 'declare variable $name external; concat("Hello, ", $name)' --var name=Tom
```

## Arguments

### `code`

Required. A file path by default; use `--xquery` or `--javascript` for inline code.
The file extension determines the language when evaluating a file.

## Options

### `--xquery`, `-x`

Treat `code` as inline XQuery. Cannot be combined with `--javascript`.

### `--javascript`, `-j`

Treat `code` as inline JavaScript. Cannot be combined with `--xquery`.

### `--var`

Bind an external variable using `name=value`. Repeat the option for several
variables. Values are supplied as strings; convert them in your query as needed.
For an XQuery variable in a namespace, use its expanded name:

```sh
ml eval -x 'declare namespace local="urn:example";
  declare variable $local:days external;
  xs:integer($local:days) + 1' --var '{urn:example}days=5'
```

### `--database`, `-d`

Content database in which to evaluate the code. When omitted, use the REST
App Server's default content database. The user must have permission to access it.

### `--txid`, `-t`

Run within an existing multi-statement transaction. This command does not create,
commit or roll back that transaction.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings. For example, `-c content` selects a named connection and
`-c 8100` uses port 8100.

See also [global options](../cli.md#global-options).
