# CTS result objects — revised design

Status: design only, revised 2026-09-25. Supersedes the earlier proposal with
twin methods, metadata envelopes and eager parsing. No runtime change this turn.

## 1. One service operation, two existing API layers

- CtsService.search converts native response parts into lazy SearchHit objects.
- CtsService.values converts parts into lazy ValueHit objects.
- CtsService.uris can use ValueHit for its string items, without a separate model.
- estimate remains a scalar count; no wrapper hierarchy for every operation.
- No search_hits, value_entries, uri_entries or with_metadata flag.
- Native builders remain expressions. Call eval.expression(Cts.search(...)) or
  eval.expression(Cts.values(...)) for the existing plain parsed output; use
  output_type=bytes for payload bytes, or rest.eval.post for the HTTP response.

Both paths reuse the same native builder. The service additionally wraps the
selected expression to return (hit, cts:score(hit)) or (value, cts:frequency(value))
pairs in one request. That wrapper and the matching decoder belong to the
service, not to the native builder or generic eval.expression. Users of
eval.expression never receive extra score/frequency parts automatically.
CTS services retain multipart payload bytes and headers before typed parsing
or singleton collapse. Reuse compile/transport/error handling; do not parse then
reserialize. With projection, emit (projected node, original hit score) for each
projected node, after range/index; zero projected nodes emit no pair.

Confirmed collection contract: preserve [] for no results, a single result
object for one item, and a list for multiple items. index=1 returns one object
or []. JSON arrays remain content inside one result object. The user explicitly
selected this contract on 2026-09-25; do not introduce always-list semantics.

## 2. What is actually transmitted?

cts:search returns a sequence of nodes, not records containing content and score.
In MarkLogic's evaluation context, cts:score can access the node's score;
cts:frequency accesses information associated with a lexicon result.
Those associations do not automatically become serialized result fields.

POST /v1/eval returns multipart results with individual content/type headers.
A local read-only probe on MarkLogic 10.0-11 observed:

| Evaluated result | Headers on the returned part |
| --- | --- |
| Stored document from cts:search | Content-Type, X-Primitive=document-node(), X-URI |
| Stored element from cts:search | Content-Type, X-Primitive=element(), X-URI, X-Path |
| Child element projected from a search hit | Content-Type, X-Primitive=element(), X-URI, X-Path |
| cts:values(cts:uri-reference()) item | Content-Type, X-Primitive=string |
| cts:uris() item | Content-Type, X-Primitive=string |

No score or frequency header was returned. Explicitly returning cts:score or
cts:frequency yielded a separate integer part. No documents were written during
these probes; only headers were inspected. These are ML10 observations, not a
claim that every result kind/version has identical headers.

Consequences:

- The later agreed design explicitly permits service-side cts:score and
  cts:frequency extraction within the same request. These are integer response
  parts, not imaginary headers. Missing or malformed partners are decoding errors,
  never substituted with 0; legitimate score/frequency 0 must be preserved.
- Decode pairs before generic parsing/collapse; validate even part count and
  the integer partner's primitive type. Leave content bytes unparsed.
- Preserve X-URI/X-Path from each returned node; no xdmp:node-uri request is needed.
  Normalize absent X-Path to '/' for document-node() only. Other missing paths
  remain None rather than falsely describing a non-document as a document.
- Native builders and generic eval.expression remain free of this service
  transport wrapper. No second HTTP request or general metadata envelope.

References:
[eval response](https://docs.marklogic.com/REST/POST/v1/eval),
[cts:score](https://docs.marklogic.com/cts:score),
[cts:frequency](https://docs.marklogic.com/cts:frequency).

## 3. Minimal public model: content plus real response headers

Provisional names: SearchHit and ValueHit in mlclient.models. Avoid Slice/Part:
a search item may be a whole document, and Part can be mistaken for a transport
multipart part. Both have the same content access vocabulary; ValueHit does not
need a redundant value alias just to rename content.

- content_bytes: bytes of this response part, initially unchanged.
- content_string: lazy decoding, no XML/JSON parsing; None for binary, matching
  BinaryDocument. Respect the payload's encoding and existing decoding rules.
- content: lazy typed parsing, cached after first access.
- headers: read-only view or defensive copy of the actual per-part headers.
- source_uri / source_path: optional convenience accessors for X-URI / X-Path
  with '/' fallback for document nodes; these never trigger a query.
- SearchHit.score / ValueHit.frequency: integer decoded from the paired part.
  URI/path identify the returned node; score describes its original search hit.
  No separate metadata record.

No SearchHitMetadata, LexiconEntryMetadata, synthetic positions, completeness
flags, generic metadata envelope or unpack-to-metadata operation. Plain
hit.content and hit.content_bytes already provide content decomposition.
Headers are HTTP transport information, not MarkLogic document metadata.

Do not subclass Document: a search result does not promise document identity,
permissions, collections or writable whole-document content. Share actual
content/serialization logic where needed, without making services import private
model helpers. A small public shared content class is justified only if it
removes real duplication from both Document and these models; no speculative
abstract result hierarchy.

## 4. Lazy parsing, including XML and JSON

The constructor stores bytes and headers only. It does not decode payloads,
parse XML/JSON, instantiate an intermediate parsed Document, or discard bytes.
Multipart splitting still happens; this is lazy payload parsing, not a streaming
or zero-copy guarantee.

| Payload | content on first access |
| --- | --- |
| XML document node | xml.etree.ElementTree.ElementTree |
| XML element node | xml.etree.ElementTree.Element |
| JSON object | dict |
| JSON array | list |
| JSON scalar/null | corresponding scalar / None |
| Typed atomic value | existing primitive conversion (e.g. Decimal, int, date) |
| Text / binary | str / bytes |

XMLDocument itself always exposes ElementTree; result objects additionally retain
the document-versus-element distinction provided by X-Primitive. This matches
the existing evaluator's native node distinction instead of pretending an
element is a complete stored document. Both provide findall for local XPath.

Use a dedicated unparsed sentinel. None, False, 0, an empty dict/list and empty
text are valid parsed values, not evidence that parsing has not happened.

Mirror Document's cache semantics: bytes access is cheap, decoded strings and
parsed content are cached independently. Parsing must not invalidate the original
bytes. If callers mutate parsed content, provide the existing invalidate()
pattern to drop stale serialized caches and serialize the modified content on
subsequent conversion. Without invalidation, original bytes remain available,
just as with Document. No silent eager reserialization on every access.

Malformed XML/JSON fails when content/xpath is accessed, not when the response
wrapper is constructed. HTTP failures and malformed multipart framing still
fail immediately. Standalone XML attributes/text and unknown primitive types
need wire probes; do not feed non-element XML fragments into fromstring blindly.

## 5. XPath mirrors XMLDocument

SearchHit.xpath(expr, **namespaces) performs:

    self.content.findall(expr, namespaces or None)

This triggers the first XML parse if necessary, then reuses the cached tree or
element. Return exactly the list from findall. Namespaces have the same calling
convention as XMLDocument. Non-XML results raise TypeError; native invalid-path
errors from ElementTree are not swallowed.

No full XPath engine, new dependency or hidden server evaluation.
This local XPath remains separate from search(xpath=...), which projects on
the server before transport.

Proposed usage (not yet implemented):

    hits = cts.search(expression="/p:product",
                          namespaces={"p": "urn:products"})
    hit = hits[0]
    payload = hit.content_bytes             # no decode/parse
    xml = hit.content                      # Element, parsed once
    titles = hit.xpath(".//p:title", p="urn:products")

    values = cts.values(reference)
    original = values[0].content_bytes      # still bytes
    number = values[0].content              # typed lazily

    products = cts.search(query=json_query)
    product = products[0].content           # dict for a JSON object
    name = product["name"]

## 6. Document conversion is not part of the initial result API

Remove as_document from this proposal. Content access/conversions work without
it, and the result is not a DocumentsService read. Also remove the former safety
discussion as a model requirement: no automatic write operation is introduced.

For clarity, content-only Document construction is technically possible without
a source URI: existing Document constructors permit uri=None. So lack of URI
does not make conversion impossible; it just cannot recreate the original stored
document's identity or metadata. If a caller needs a new document, they can use
the existing Document factory explicitly with content/type and their chosen URI.

Optional X-URI describes provenance, not a destination for writing a fragment.
Do not silently turn it into Document.uri.

## 7. Implementation checklist

- [x] Preserve empty/singleton/list cardinality, including index (user confirmed).
- [ ] Decode multipart parts to bytes+headers before any generic typed parsing.
- [ ] Reuse native compilation, transport options and shared error handling.
- [ ] Probe ML10/11/12 XML document/element/attribute/text, JSON object/array/null,
  binary, empty results and atomic types; preserve only received headers.
- [ ] Verify no XML/JSON parse on construction, content_bytes or content_string.
- [ ] Verify parse once, including JSON null/false/0/empty values.
- [ ] Verify XML ElementTree/Element distinction, namespace findall, errors,
  cache invalidation and byte retention.
- [ ] Verify service methods return wrappers while eval.expression still returns
  its existing types; only services inject score/frequency pairing, in one request.
- [ ] Keep sync/async contracts aligned, public imports explicit and mocks local.
- [ ] Update service docs/tests together when implementing the changed contract.

Only this design and its tracker changed in the current turn. Runtime behavior
and earlier implementation-test results are unchanged.

## 8. Search node contract: verified through the current public API

Read-only probes on ML10.0-11, 2026-09-25, used CtsService.search and
ml.eval.expression(Cts.valid_extract_path(...)):

| Input | Result |
| --- | --- |
| expression='/fn:string()' | MLCLIENT-INVALID-PATH |
| expression='/a/fn:string()' | MLCLIENT-INVALID-PATH |
| expression='/a', xpath='/fn:string()' | MLCLIENT-INVALID-PATH |
| expression='/a', xpath='fn:string()' | MLCLIENT-INVALID-PATH |
| expression=xs.string('atomic') | XDMP-UNSEARCHABLE |
| expression='/a' | Element result |

The native search return contract is node()*. Restricted extraction paths do
not make search into a general atom-producing evaluation API. A text node,
attribute node or JSON scalar node remains a node on the server even if its
Python content representation is str/int/bool/None. Atomic lexicon values belong
to values/field_values/etc., not the SearchHit node contract.

The validator accepted '/a/text()' and '/a/@*'; node does not mean only element
or document. Thus the earlier atomic-result caveat was misplaced for search,
but missing X-Path must still be interpreted with the actual node primitive,
not assumed to mean document-node(). These probes are not an ML11/12 verification.

Reference: [cts:search node return type](https://docs.marklogic.com/cts:search).

## 9. Required documentation and example conventions

- ALWAYS name a CtsService or AsyncCtsService instance 'cts' in user examples
  and documentation. Use Cts.search(...) for native builder examples when both
  layers appear together; do not use 'service' for the service variable.
- Explain expression (the searchable input to cts:search), server-side xpath
  projection after range/index, source_path (response node location), and local
  hit.xpath (ElementTree.findall). They are different concepts.
- Document native builder -> eval.expression -> plain parsed output versus
  service call -> internal paired transport -> lazy result objects. Include
  score/frequency behavior and ensure users never manually pair multipart parts.
- Demonstrate XML content/content_bytes/content_string, lazy JSON dict parsing,
  namespace-aware local xpath, and document-node source_path='/' fallback.
- Do not advertise the proposed wrapper methods as already implemented.

## 10. Later phase: all result-producing CTS functions execute in the service

DEFERRED until after the current commits, as requested. The service must not
stop at search/values/uris/estimate. Every supported function that performs a
search/lookup/computation and returns actual results must execute in both sync
and async services. field_values is a confirmed missing override.

Query constructors such as path_range_query keep returning composable expressions;
likewise constructors of references, ordering clauses and other query-building
values must remain composable. Do not classify solely by Python return annotation
(all builders return expressions), method suffix, or whether the native return
type says 'value'. Use each native function's semantic role.

- [ ] Inventory every method in the supported Cts catalog and record whether it
  constructs a query component or executes a result-producing operation.
- [ ] Cover all result operations, including field_values, other lexicon families,
  matching functions, tuples/co-occurrences and aggregates; do not silently leave
  them as inherited builders. Explicitly review predicates/utility operations.
- [ ] Map native result shapes to node hits, frequency-bearing lexicon values,
  scalar results or structured results. Do not blindly apply score/frequency to
  every function, or range/index to scalar results.
- [ ] Add matching sync/async overrides preserving native parameters and sharing
  compilation, transport, namespaces and error handling.
- [ ] Guard the classification against the full builder catalog in tests so
  newly added result functions cannot silently lack service execution support.
- [ ] Document nesting: use Cts.field_values(...) to compose a native expression;
  cts.field_values(...) executes immediately once this phase is implemented.
