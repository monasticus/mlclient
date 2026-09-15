# http

Send an HTTP request and print its response body. Use lowercase method names;
method matching is case-insensitive.

```sh
ml http get /v1/documents uri=/doc.json
ml http get /v1/documents uri=/doc.json --include --pretty
```

Supply headers with `name:value`, query parameters with `name=value`, and a body
with `--body`:

```sh
ml http put /v1/documents uri=/doc.json \
  Content-Type:application/json -b '{"hello":"world"}'
ml http put /v1/documents uri=/doc.xml \
  Content-Type:application/xml -b @./doc.xml
ml http delete /v1/documents uri=/doc.xml
```

To use the Manage API, select its configured connection explicitly:

```sh
ml http get /manage/v2/hosts -c manage view=status format=json
```

## Arguments

### `method`

Required. An HTTP method such as `get`, `head`, `post`, `put`, `delete` or `patch`.

### `endpoint`

Required. An endpoint path such as `/v1/documents`. It may contain a query string.
The path does not select a connection automatically: `/manage/v2/*` still needs
`-c manage` (or the appropriate port).

### `params`

Optional, repeatable query parameters and headers. A `key=value` token adds a query
parameter; a `key:value` token adds a header. Quote tokens containing spaces.
Repeated query keys preserve every value. Header names are case-insensitive;
the last value wins.

```sh
ml http get /v1/documents uri=/one.xml uri=/two.xml Accept:application/xml
```

## Options

### `--body`, `-b`

Request body as literal text, an existing file path, or an explicit `@path`.
Files are read as bytes, preserving binary content and line endings. An explicit
`@path` must exist and be readable. Text, including JSON, is sent unchanged.
Set the appropriate `Content-Type` header yourself.

### `--include`, `-i`

Print the HTTP status line and response headers before the body. A `head` request
always prints them because it has no response body.

### `--pretty`, `-p`

Format JSON and element-only XML with two-space indentation. Invalid JSON/XML,
mixed XML content and `xml:space="preserve"` are left unchanged.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings. For example, `-c content` selects a named connection and
`-c 8100` uses port 8100.

## Responses and errors

Output is decoded response text. Responses are printed before a 4xx/5xx error is
reported with a nonzero exit code. Redirect responses are displayed without
following them and do not count as HTTP errors. With `--include`, the status line
uses the actual HTTP protocol version.

See also [global options](../cli.md#global-options).
