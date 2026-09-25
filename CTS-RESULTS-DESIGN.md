# CTS result objects — agreed contract

Revised 2026-09-25. **The latest user decision supersedes lazy payload parsing:**
models receive already parsed content. MLResponseParser is the only parser.
Implemented on feature/cts-service; verification is recorded below.

## 1. Content models, not transport or parsing models

Public models in `mlclient.models`:

- `SearchHit(content, *, score, content_bytes=None, encoding="utf-8",
  source_uri=None, source_path="/")`.
- `ValueHit(content, *, frequency, content_bytes=None, encoding="utf-8")`.
- `ResultContent` shares only content storage, original-text decoding and local
  XML `findall`. It has no parsing dispatch, primitive-conversion table or headers.

`content` is exactly the value supplied by MLResponseParser. Models do not parse
it on construction or access, wrap it in Document, or infer its type from a URI.
They need no content-type/primitive-type descriptor for later parsing.

The service can access each MultipartPart's original bytes directly, so it
always supplies `content_bytes` without reserialization. `content_string` decodes
this original snapshot using the supplied encoding; it returns None for binary
content or when no snapshot was supplied to a manually constructed model.

Original bytes are a **snapshot**, not a synchronized serialization cache.
Mutating a parsed dict/XML tree does not rewrite them. No `invalidate`, lazy
parser sentinel or model-level serializer is needed. This intentionally replaces
the earlier proposal mirroring Document's lazy caches. Document is unchanged.

No raw/parsed twin service methods, generic metadata bag, HTTP headers property,
`as_document`, or speculative abstract hierarchy. REST remains the raw-header API.

## 2. One parser and one request

The service wraps the selected native expression into pairs:

- search: `(hit, cts:score(hit))`;
- frequency-bearing lexicons: `(value, cts:frequency(value))`.

The pair decoder validates an even number of parts and integer measure partners.
It calls the public `MLResponseParser.parse_part` for each payload and supplies
that parsed value plus the unchanged payload bytes to the model. Score/frequency
are never guessed from content and malformed/missing partners are never 0.
Legitimate 0 and empty text/binary payloads remain real result items.

Generic eval parsing and service results use the same primitive conversion
table and XML/JSON implementation in MLResponseParser. Malformed content fails
during service execution, not later on `.content`. HTTP failures use the shared
raise_for_status implementation before any successful-result decoding.

Native builders `Cts.search`, `Cts.values`, etc. remain plain expressions:
`ml.eval.expression(Cts.search(...))` does NOT inject score/frequency parts.
Use `output_type=bytes` there for native per-item bytes. Services always convert
their result models, rather than accepting raw output_type overrides.

For server projection: **search → range/index → capture original score → project
each hit → emit each projected node with that score**. No projection emits no
pair; multiple projected nodes repeat the original score. No second request,
custom JSON/XML envelope or xdmp:node-uri lookup is introduced.

## 3. Cardinality and provenance

- No results: `[]`.
- One result: one SearchHit/ValueHit, including `index=1`.
- Multiple results: a list of result objects.
- A JSON array remains one hit's content, never the outer result list.
- source_uri comes from X-URI when present, otherwise None.
- source_path preserves X-Path; an absent path becomes `/`, as requested.
  This is a location fallback, NOT proof that the primitive is document-node().

Source URI/path describe the returned node, not write permissions, document
metadata or a safe target for replacing a whole document.

## 4. Every content kind is supported

| Received payload | Parsed content |
| --- | --- |
| XML document node | ElementTree |
| XML element | Element |
| JSON object/array | dict/list |
| JSON number/boolean/null | corresponding Python scalar/None |
| JSON property as text/plain + text() | str |
| Text document/text node/XML attribute | str |
| Comment/processing instruction as text/plain | textual serialization |
| Binary | unchanged bytes |
| Atomic lexicon values | existing MLResponseParser conversions, e.g. Decimal |
| Unrecognized primitive | existing parser fallback, retaining original bytes |

Do not parse an unquoted JSON property string with json.loads because its URI
ends in .json. XML text/attributes are not standalone XML elements. Binary data
must not be decoded as UTF-8 or converted to base64. Every kind can carry score;
the Python type of content does not affect score extraction.

Default search may return mixed XML/JSON/TXT/binary results. Non-default
expression/xpath is not a client-side type filter: a valid text-node selection
can still yield str. Native validation determines searchable/extractable paths.
Unsupported native functions/indexes report normal MarkLogic errors.

`cts:search` returns node()*. Text and JSON scalar nodes are still nodes, although
their Python content is scalar. Arbitrary atom-producing paths such as
`/fn:string()` remain invalid; supporting scalar content does not change that.

## 5. XPath and examples

`hit.xpath(expr, **namespaces)` directly mirrors
`hit.content.findall(expr, namespaces or None)` for ElementTree/Element.
There is no parsing or HTTP request here. Non-XML content raises TypeError.

Distinguish all four concepts in user docs:

1. `search(expression=...)`: searchable input to native cts:search.
2. `search(xpath=...)`: server-side projection after range/index.
3. `hit.source_path`: location of the returned node, including `/` fallback.
4. `hit.xpath(...)`: local ElementTree.findall on parsed XML content.

Service instances are ALWAYS named `cts` in examples and documentation.
Use `Cts.method(...)` for native builder composition when both layers appear.

## 6. Complete service catalog

All 191 supported Cts methods have an explicit policy in the owning service
tests: 91 constructors, 35 frequency-bearing lexicon lookups, 64 ordinary
result-producing operations, and search. All 100 result operations execute in
both sync and async services; field_values is included.

Query/reference/order/geometry/entity-dictionary constructors remain composable.
Scalar utilities, aggregates and structured results execute without fabricated
score/frequency fields. Tuples/co-occurrences/ranges retain their native parsed
structure; no universal result wrapper is imposed. Only search and value-sequence
methods offer range/index, not scalar operations.

The native lexicon `map` option produces a different shape, not a sequence of
individual values. Frequency-bearing services reject actual map results with
MLCLIENT-LEXICON-MAP, including options provided as expressions. Native map output
remains available through eval.expression(Cts...). No raw twin method is added.

Tests compare the explicit inventory with the full builder catalog and verify
sync/async execution and request routing, preventing silently inherited lookups.

## 7. Evidence and remaining verification

User-supplied wire examples (2026-09-25):

| Payload | Content-Type | X-Primitive | X-URI | X-Path |
| --- | --- | --- | --- | --- |
| b | text/plain | text() | /c.json | /text("a") |
| {"a":"b"} | application/json | object-node() | /c.json | absent |
| abcd | text/plain | text() | /d.txt | absent |

Local ML10.0-11 read-only probes additionally confirmed XML attributes, comments,
processing instructions, JSON number/boolean/null/array nodes and binary
`00 FF 41` bytes. Binary had application/x-unknown-content-type + binary().
The integration fixture writes binary through DocumentsService and cleans up
its isolated documents in finally; it requires no permanent manual fixture.

- [x] Confirm singleton policy and parsed-content architecture with the user.
- [x] Implement one parser, models receiving parsed content, and original bytes.
- [x] Implement sync/async result-operation overrides and catalog inventory.
- [x] Final parsed-model revision: 2962 unit tests pass with 100% line coverage.
- [x] Run 19 live scenarios on ML10.0-11, including positive score projection.
- [x] Ruff, strict docs (227 HTML pages), wheel/sdist and outside-checkout imports
  and CLI checks pass. No new lint suppression was needed for the final models.
- ML11/12 environments are not running locally; their existing CI matrix remains
  the cross-version verification path, not a claimed local pass.

References: [cts:search](https://docs.marklogic.com/cts:search),
[cts:frequency](https://docs.marklogic.com/cts:frequency),
[eval response](https://docs.marklogic.com/REST/POST/v1/eval).
