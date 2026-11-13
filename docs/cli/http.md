# http

![Http demonstration](../assets/gifs/http.gif)

Send an HTTP request and print its decoded response body without reformatting
by default. Use `--pretty` to format JSON and XML with two-space indentation.
Unlike `http`, `eval` and `sample` format results by default and offer `--no-pretty`
to disable formatting. Use lowercase method names; method matching is
case-insensitive.

```sh
ml http get /v1/documents uri=/doc.json
ml http get /v1/documents uri=/doc.json --include
ml http get /v1/documents uri=/doc.json --pretty
```

Supply headers with `name:value`, query parameters with `name=value`, and a body
with `--body`:

```sh
ml http put /v1/documents uri=/doc.json \
  Content-Type:application/json -b '{"hello":"world"}'
ml http put /v1/documents uri=/doc.xml -b @./doc.xml
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

MarkLogic parameter names with a colon are query parameters when the token
contains `=`: `rs:`, `trans:`, `perm:`, `prop:`, `value:`, `bind:` and the
extension method declarations `get:`, `put:`, `post:` and `delete:`. Every other
token is split at its first `=` or `:`, so a header value may contain `=`.

```sh
ml http get /v1/resources/my-extension rs:name=value
ml http get /v1/documents uri=/doc.json transform=my-transform trans:mode=draft
ml http put /v1/documents uri=/doc.json perm:rest-reader=read -b @./doc.json
ml http post /v1/documents Content-Type:'multipart/mixed; boundary=xyz' -b @./batch
```

## Options

### `--body`, `-b`

Request body as literal text, an existing file path, or an explicit `@path`.
Files are read as bytes, preserving binary content and line endings. An explicit
`@path` must exist and be readable. Text, including JSON, is sent unchanged.
A file body gets the `Content-Type` of its extension from MarkLogic's mimetype
table (for example `.json` is `application/json`, `.xml` is `application/xml`).
A `Content-Type` header you give always wins. A literal body, or a file with an
extension the table does not know, is sent without one; set it yourself.

### `--include`, `-i`

Print the HTTP status line and response headers before the body. A `head` request
always prints them because it has no response body.

### `--pretty`, `-p`

Format JSON and element-only XML with two-space indentation. Disabled by default.
When the response has no Content-Type or uses `text/plain`, detect JSON/XML
from the body.
Invalid JSON/XML is left unchanged. Mixed XML content and `xml:space="preserve"`
subtrees are not re-indented; the surrounding XML is still formatted.
An existing XML declaration is preserved verbatim; none is added when absent.

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

## Responses and errors

Output is decoded response text. A 4xx/5xx response prints its body and exits
with code 1. An error response without a body prints one line to stderr instead,
for example `HTTP 503 Service Unavailable for http://localhost:8000/v1/ping`.
With several environments, that line fills the environment's column. Redirect responses are displayed without
following them and do not count as HTTP errors. With `--include`, the status line
uses the actual HTTP protocol version.

See also [global options](index.md#global-options).
