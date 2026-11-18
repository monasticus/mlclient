# eval

![Query evaluation demonstration](../assets/gifs/eval.gif)

Run XQuery or server-side JavaScript and print the result.
XML and JSON results are formatted with two-space indentation by default.
An existing XML declaration is preserved verbatim; none is added when absent.
Mixed XML content and `xml:space="preserve"` subtrees are not re-indented;
the surrounding XML is still formatted with two-space indentation.

```sh
ml eval '"Hello World!"'
ml eval -j '"Hello World!"'
ml eval ./query.xqy
ml eval -x '<root><item>one</item></root>' --no-pretty
```

Use `-d` to select a content database, or pass external variables with `--var`:

```sh
ml eval ./query.xqy -d Documents
ml eval -x 'declare variable $name external; concat("Hello, ", $name)' --var name=Tom
```

## Arguments

### `code`

Required. Without `--xquery` or `--javascript`, the argument is read as follows:

| Argument | Evaluated as |
|---|---|
| `@path` | The file at `path`; an error if it does not exist |
| An existing file with a code extension (`xq`, `xql`, `xqm`, `xqu`, `xquery`, `xqy`, `js`, `sjs`) | The file, in the language of its extension |
| An existing file with another extension, e.g. `notes.txt` | An error: unknown file extension |
| A name ending with a code extension that does not exist, e.g. `quer.xqy` | An error: file not found, so a mistyped file name never runs as code |
| Anything else, e.g. `'1+1'` | Inline XQuery |

With `--xquery` or `--javascript` the argument is always inline code, even when it
names an existing file.

## Options

### `--xquery`, `-x`

Treat `code` as inline XQuery, even when it names an existing file.
Cannot be combined with `--javascript`.

### `--javascript`, `-j`

Treat `code` as inline JavaScript, even when it names an existing file.
Cannot be combined with `--xquery`.

### `--var`

Bind an external variable using `name=value`. Repeat the option for several
variables. Names cannot be empty or whitespace only. Values may be empty;
only the first `=` separates the name, so a value may contain `=`.
Values are supplied as strings; convert them in your query as needed.
For an XQuery variable in a namespace, use its expanded name:

```sh
ml eval 'declare namespace local="https://monasticus.com/mlclient/examples/example";
  declare variable $local:days external;
  xs:integer($local:days) + 1' --var '{https://monasticus.com/mlclient/examples/example}days=5'
```

### `--database`, `-d`

Content database in which to evaluate the code. When omitted, use the REST
App Server's default content database. The user must have permission to access it.

### `--txid`, `-t`

Run within an existing multi-statement transaction. This command does not create,
commit or roll back that transaction.

### `--no-pretty`

Print each result without reformatting XML or JSON, for example when piping output
to another tool. Plain text and other scalar results are always printed unchanged.

### `--timeout`

Seconds to wait for MarkLogic. A number sets all four HTTP timeout components
(connect, read, write and pool) for this request; `0` disables the timeout.
Without the option the client defaults apply: 5 seconds to connect, 60 seconds
to read. See [Timeouts](../advanced/http/timeouts.md).

This command sends `POST` requests, which the default retry policy does not
retry. See [timeout and retry details](../advanced/http/timeouts.md#command-line)
for how the per-attempt limit relates to total waiting time.

A read or write timeout only stops the client from waiting. MarkLogic may keep
running the request, so an update may still commit after the command has failed. The command
prints one line to stderr and exits with 1:

```text
Request timed out after 60s - it may still be running on the server
```

Connection and pool timeouts identify the expired connection stage instead of
warning that the request may still be running.

Before you run an update again, check on the server whether it is still running
or has committed, for example in the Monitoring dashboard or with
`xdmp:server-status`.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`. Repeat the option to select several environments,
for example `-e dev -e test`. Explicit names replace the `local` default;
duplicates run only once, in their first-given order.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings. For example, `-c content` selects a named connection and
`-c 8100` uses port 8100.

See also [global options](index.md#global-options).
