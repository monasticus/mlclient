# invoke

![Module invocation demonstration](../assets/gifs/invoke.gif)

Run an XQuery or server-side JavaScript module installed in MarkLogic and print
the result. Results are printed and formatted as in [eval](eval.md).

```sh
ml invoke /ext/report.xqy
ml invoke /ext/words.sjs --var word1=hello --var word2=world
ml invoke /ext/report.xqy -d Documents --no-pretty
```

The module path resolves against the modules database or directory of the App
Server receiving the request, so select the connection whose App Server has the
module installed:

```sh
ml invoke -c app-services /ext/report.xqy
```

## Arguments

### `module`

Required. The path of the module, such as `/ext/report.xqy`. Its suffix selects
the language: `.sjs` runs as JavaScript, `.xqy` as XQuery.

## Options

### `--var`

Bind an external variable using `name=value`. Repeat the option for several
variables. Names cannot be empty or whitespace only. Values may be empty;
only the first `=` separates the name, so a value may contain `=`.
Values are supplied as strings; convert them in your module as needed. For an
XQuery variable in a namespace, use its expanded name, as in [eval](eval.md#-var).

### `--database`, `-d`

Content database in which to invoke the module. When omitted, use the REST
App Server's default content database. The user must have permission to access it.

### `--txid`, `-t`

Run within an existing multi-statement transaction. This command does not create,
commit or roll back that transaction.

### `--no-pretty`

Print each result without reformatting XML or JSON, for example when piping output
to another tool. Plain text and other scalar results are always printed unchanged.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`. Repeat it to invoke the module concurrently in
several environments and compare results, for example
`ml invoke /ext/report.xqy -e dev -e test`. Repeated names are used once.
Each target App Server must have the module installed; any failed environment
gives exit status 1 while successful peers remain visible.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings. For example, `-c content` selects a named connection and
`-c 8100` uses port 8100.

See also [global options](index.md#global-options).
