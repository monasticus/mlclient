# sample

Inspect a few XML or JSON documents or nodes without writing a query.
The command evaluates `cts.search(...).pos([1, limit])` with `ml.eval.expression`
on the selected connection's content database. It returns content without score
or source-location metadata and does not modify documents. XML is the default,
and the limit defaults to 1. Results are formatted with two-space indentation by
default; use `--no-pretty` to retain the server's formatting.

```sh
ml sample order
ml sample '/order/item' --limit 3
ml sample '*:order' -c content
ml sample / --json
ml sample address --json
ml sample / --json --limit 2 --no-pretty
```

## Arguments

### `path`

Optional root name or XPath, defaulting to `/` (whole documents). A bare name such
as `order` becomes `/order`. Input containing a slash or starting with `.` is
passed unchanged. For a namespace-independent XML root name, use `*:order`.

Paths must be fully searchable by MarkLogic's `cts:search`. This is a database
XPath, not a document URI or a JSONPath expression. Empty input is rejected.
An empty result produces no output and succeeds.

## Options

### `--limit`, `-l`

Integer maximum number of returned nodes from `1` to `100`, defaulting to `1`.
Values outside this range are rejected before a request is made. Selection
happens on the server via `.pos([1, limit])`, not by truncating downloaded results.
The limit counts selected nodes, which are not necessarily whole documents.
Results follow the normal CTS search order; this is not random sampling.

### `--json`

Select JSON documents instead of XML using the CTS `format-json` option.
Without this flag the search uses `format-xml`.

JSON documents do not need a named outer property: `ml sample / --json` prints
whole documents. To inspect an object property, use `ml sample address --json`
or an explicit path such as `/customer/address`. Paths select native JSON nodes;
the command does not convert XML to JSON or JSON to XML.
See MarkLogic's [JSON XPath guide](https://docs.progress.com/bundle/marklogic-server-develop-server-side-apps-12/page/topics/json.html).

### `--no-pretty`

Disable the default two-space indentation. Each selected result is printed on its
own line, with no score or source-location metadata. JSON arrays remain single
results rather than being split into separate samples.

Each result is decoded as text without model conversion or re-serialization.
`--no-pretty` preserves the server's formatting. With pretty-printing enabled,
an existing XML declaration is preserved verbatim; none is added when absent.
Mixed XML content and `xml:space="preserve"` are not re-indented.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings.

See also [global options](../cli.md#global-options).
