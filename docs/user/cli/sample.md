# sample

Inspect a few XML or JSON documents or nodes without writing a query.
By default, print one XML result from the selected connection's content database.
Use `--json` (`-j`) for JSON, a path to select specific content, and `--limit` to
show more results. The command reads data without modifying documents.
Results use two-space indentation by default; `--no-pretty` retains the server's
formatting.

```sh
ml sample order
ml sample '/order/item' --limit 3
ml sample '*:order' -c content
ml sample / -j
ml sample address --json
ml sample / --json --limit 2 --no-pretty
```

## Arguments

### `path`

Optional root name or XPath, defaulting to `/` (whole documents). A bare name such
as `order` becomes `/order`. Input containing a slash or starting with `.` is
passed unchanged. For a namespace-independent XML root name, use `*:order`.

Use a database XPath supported by MarkLogic. Document URIs and JSONPath
expressions are not accepted. Empty input is rejected.
An empty result produces no output and succeeds.

## Options

### `--limit`, `-l`

Integer maximum number of returned nodes from `1` to `100`, defaulting to `1`.
Values outside this range are rejected. The limit counts selected nodes, which
may be whole documents or parts of documents. Results are returned in search
order rather than chosen randomly.

### `--json`, `-j`

Select JSON documents instead of the default XML documents.

JSON documents do not need a named outer property: `ml sample / --json` prints
whole documents. To inspect an object property, use `ml sample address --json`
or an explicit path such as `/customer/address`. Paths select native JSON nodes;
the command does not convert XML to JSON or JSON to XML.
See MarkLogic's [JSON XPath guide](https://docs.progress.com/bundle/marklogic-server-develop-server-side-apps-12/page/topics/json.html).

### `--no-pretty`

Disable the default two-space indentation. Each selected result is printed on its
own line, with no score or source-location metadata. JSON arrays remain single
results rather than being split into separate samples.

`--no-pretty` preserves the server's formatting. With pretty-printing enabled,
an existing XML declaration is preserved verbatim; none is added when absent.
Mixed XML content and `xml:space="preserve"` subtrees are not re-indented;
the surrounding XML is still formatted with two-space indentation.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings.

See also [global options](../cli.md#global-options).
