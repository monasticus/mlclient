"""Check the documented FN catalog and native argument routing."""

import inspect

import pytest

from mlclient.functions.xqy import fn
from mlclient.functions.xqy.expressions import CompilationContext

# Native MarkLogic 12 reference catalog, including legacy/context-only entries.
CATALOG = [
    ("abs", "abs"),
    ("adjust-date-to-timezone", "adjust_date_to_timezone"),
    ("adjust-dateTime-to-timezone", "adjust_date_time_to_timezone"),
    ("adjust-time-to-timezone", "adjust_time_to_timezone"),
    ("analyze-string", "analyze_string"),
    ("avg", "avg"),
    ("base-uri", "base_uri"),
    ("boolean", "boolean"),
    ("ceiling", "ceiling"),
    ("codepoint-equal", "codepoint_equal"),
    ("codepoints-to-string", "codepoints_to_string"),
    ("collection", "collection"),
    ("compare", "compare"),
    ("concat", "concat"),
    ("contains", "contains"),
    ("count", "count"),
    ("current", "current"),
    ("current-date", "current_date"),
    ("current-dateTime", "current_date_time"),
    ("current-group", "current_group"),
    ("current-grouping-key", "current_grouping_key"),
    ("current-time", "current_time"),
    ("data", "data"),
    ("dateTime", "date_time"),
    ("day-from-date", "day_from_date"),
    ("day-from-dateTime", "day_from_date_time"),
    ("days-from-duration", "days_from_duration"),
    ("deep-equal", "deep_equal"),
    ("default-collation", "default_collation"),
    ("distinct-nodes", "distinct_nodes"),
    ("distinct-values", "distinct_values"),
    ("doc", "doc"),
    ("doc-available", "doc_available"),
    ("document", "document"),
    ("document-uri", "document_uri"),
    ("element-available", "element_available"),
    ("empty", "empty"),
    ("encode-for-uri", "encode_for_uri"),
    ("ends-with", "ends_with"),
    ("error", "error"),
    ("escape-html-uri", "escape_html_uri"),
    ("escape-uri", "escape_uri"),
    ("exactly-one", "exactly_one"),
    ("exists", "exists"),
    ("expanded-QName", "expanded_qname"),
    ("false", "false"),
    ("filter", "filter"),
    ("floor", "floor"),
    ("fold-left", "fold_left"),
    ("fold-right", "fold_right"),
    ("format-date", "format_date"),
    ("format-dateTime", "format_date_time"),
    ("format-number", "format_number"),
    ("format-time", "format_time"),
    ("function-arity", "function_arity"),
    ("function-available", "function_available"),
    ("function-lookup", "function_lookup"),
    ("function-name", "function_name"),
    ("generate-id", "generate_id"),
    ("head", "head"),
    ("hours-from-dateTime", "hours_from_date_time"),
    ("hours-from-duration", "hours_from_duration"),
    ("hours-from-time", "hours_from_time"),
    ("id", "id"),
    ("idref", "idref"),
    ("implicit-timezone", "implicit_timezone"),
    ("in-scope-prefixes", "in_scope_prefixes"),
    ("index-of", "index_of"),
    ("insert-before", "insert_before"),
    ("iri-to-uri", "iri_to_uri"),
    ("key", "key"),
    ("lang", "lang"),
    ("last", "last"),
    ("local-name", "local_name"),
    ("local-name-from-QName", "local_name_from_qname"),
    ("lower-case", "lower_case"),
    ("map", "map"),
    ("map-pairs", "map_pairs"),
    ("matches", "matches"),
    ("max", "max"),
    ("min", "min"),
    ("minutes-from-dateTime", "minutes_from_date_time"),
    ("minutes-from-duration", "minutes_from_duration"),
    ("minutes-from-time", "minutes_from_time"),
    ("month-from-date", "month_from_date"),
    ("month-from-dateTime", "month_from_date_time"),
    ("months-from-duration", "months_from_duration"),
    ("name", "name"),
    ("namespace-uri", "namespace_uri"),
    ("namespace-uri-for-prefix", "namespace_uri_for_prefix"),
    ("namespace-uri-from-QName", "namespace_uri_from_qname"),
    ("nilled", "nilled"),
    ("node-kind", "node_kind"),
    ("node-name", "node_name"),
    ("normalize-space", "normalize_space"),
    ("normalize-unicode", "normalize_unicode"),
    ("not", "not_"),
    ("number", "number"),
    ("one-or-more", "one_or_more"),
    ("position", "position"),
    ("prefix-from-QName", "prefix_from_qname"),
    ("QName", "qname"),
    ("regex-group", "regex_group"),
    ("remove", "remove"),
    ("replace", "replace"),
    ("resolve-QName", "resolve_qname"),
    ("resolve-uri", "resolve_uri"),
    ("reverse", "reverse"),
    ("root", "root"),
    ("round", "round"),
    ("round-half-to-even", "round_half_to_even"),
    ("seconds-from-dateTime", "seconds_from_date_time"),
    ("seconds-from-duration", "seconds_from_duration"),
    ("seconds-from-time", "seconds_from_time"),
    ("starts-with", "starts_with"),
    ("static-base-uri", "static_base_uri"),
    ("string", "string"),
    ("string-join", "string_join"),
    ("string-length", "string_length"),
    ("string-pad", "string_pad"),
    ("string-to-codepoints", "string_to_codepoints"),
    ("subsequence", "subsequence"),
    ("substring", "substring"),
    ("substring-after", "substring_after"),
    ("substring-before", "substring_before"),
    (
        "subtract-dateTimes-yielding-dayTimeDuration",
        "subtract_date_times_yielding_day_time_duration",
    ),
    (
        "subtract-dateTimes-yielding-yearMonthDuration",
        "subtract_date_times_yielding_year_month_duration",
    ),
    ("sum", "sum"),
    ("system-property", "system_property"),
    ("tail", "tail"),
    ("timezone-from-date", "timezone_from_date"),
    ("timezone-from-dateTime", "timezone_from_date_time"),
    ("timezone-from-time", "timezone_from_time"),
    ("tokenize", "tokenize"),
    ("trace", "trace"),
    ("translate", "translate"),
    ("true", "true"),
    ("type-available", "type_available"),
    ("unordered", "unordered"),
    ("unparsed-entity-public-id", "unparsed_entity_public_id"),
    ("unparsed-entity-uri", "unparsed_entity_uri"),
    ("unparsed-text", "unparsed_text"),
    ("unparsed-text-available", "unparsed_text_available"),
    ("upper-case", "upper_case"),
    ("year-from-date", "year_from_date"),
    ("year-from-dateTime", "year_from_date_time"),
    ("years-from-duration", "years_from_duration"),
    ("zero-or-one", "zero_or_one"),
]


def test_fn_catalog_is_complete():
    assert {name for name in dir(fn) if not name.startswith("_")} == {
        python for _, python in CATALOG
    }


@pytest.mark.parametrize(("native", "python"), CATALOG)
def test_fn_calls_preserve_native_names_and_argument_order(native, python):
    method = getattr(fn, python)
    positional = []
    keywords = {}
    expected = []
    for parameter in inspect.signature(method).parameters.values():
        value = f"value-{parameter.name}"
        expected.append(value)
        if parameter.kind == parameter.KEYWORD_ONLY:
            keywords[parameter.name] = value
        else:
            positional.append(value)
    expression = method(*positional, **keywords)
    context = CompilationContext()
    code = expression.render(context)
    assert (
        code
        == f"fn:{native}("
        + ", ".join(f"$v{index}" for index in range(len(expected)))
        + ")"
    )
    assert list(context.variables.values()) == expected
    assert f"https://docs.marklogic.com/fn:{native}" in method.__doc__


def test_fn_optional_arguments_distinguish_absent_from_empty():
    assert str(fn.collection()).endswith("fn:collection()")
    assert str(fn.collection(None)).endswith("fn:collection(())")
    assert str(fn.string()).endswith("fn:string()")
    assert str(fn.string(None)).endswith("fn:string(())")
    assert str(fn.error(description="message")).endswith("fn:error((), $v0)")
    assert str(fn.count([], maximum=None)).endswith("fn:count((), ())")
    assert str(fn.concat("a", None, "b")).endswith("fn:concat($v0, (), $v1)")
    with pytest.raises(TypeError, match="unsupported XQuery value type"):
        fn.map(lambda item: item, [1])
