from __future__ import annotations

import pytest

from mlclient.functions.xqy import XqyCompilationContext, fn, xs


@pytest.mark.parametrize(
    ("value", "body", "variables", "declarations"),
    [
        (None, "fn:count(())", {}, ""),
        ([], "fn:count(())", {}, ""),
        ((), "fn:count(())", {}, ""),
        (
            "abc",
            "fn:count($v0)",
            {"v0": "abc"},
            "declare variable $v0 as xs:string external;\n",
        ),
        (
            [1, 2],
            "fn:count(($v0, $v1))",
            {"v0": "1", "v1": "2"},
            "declare variable $v0 as xs:integer external;\n"
            "declare variable $v1 as xs:integer external;\n",
        ),
    ],
)
def test_uniform_sequence_semantics(value, body, variables, declarations):
    assert fn.count(value).compile() == (
        'xquery version "1.0-ml";\n' + declarations + body,
        variables,
    )


@pytest.mark.parametrize(
    ("expression", "expected", "variables"),
    [
        (fn.count([1], maximum=1), "fn:count(($v0), $v1)", {"v0": "1", "v1": "1"}),
        (fn.exists([]), "fn:exists(())", {}),
        (fn.empty([]), "fn:empty(())", {}),
    ],
)
def test_render_literal_arguments(expression, expected, variables):
    context = XqyCompilationContext()
    assert expression.render(context) == expected
    assert context.variables == variables


@pytest.mark.parametrize(
    ("expression", "body", "variables"),
    [
        (fn.collection(), "fn:collection()", {}),
        (fn.collection(None), "fn:collection(())", {}),
        (fn.string(), "fn:string()", {}),
        (fn.string(None), "fn:string(())", {}),
        (fn.error(description="message"), "fn:error((), $v0)", {"v0": "message"}),
        (fn.count([], maximum=None), "fn:count((), ())", {}),
        (fn.concat("a", None, "b"), "fn:concat($v0, (), $v1)", {"v0": "a", "v1": "b"}),
    ],
)
def test_optional_arguments_distinguish_absent_from_empty(expression, body, variables):
    declarations = "".join(
        f"declare variable ${key} as xs:string external;\n" for key in variables
    )
    assert expression.compile() == (
        'xquery version "1.0-ml";\n' + declarations + body,
        variables,
    )


def test_map_rejects_a_python_callback():
    with pytest.raises(TypeError, match="unsupported XQuery value type"):
        fn.map(lambda item: item, [1])


@pytest.mark.parametrize(
    ("expression", "body", "variables"),
    [
        pytest.param(
            fn.abs(xs.string("arg")),
            "fn:abs(xs:string($v0))",
            {"v0": "arg"},
            id="abs",
        ),
        pytest.param(
            fn.adjust_date_to_timezone(
                xs.string("arg"),
                timezone=xs.string("timezone"),
            ),
            "fn:adjust-date-to-timezone(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "timezone"},
            id="adjust_date_to_timezone",
        ),
        pytest.param(
            fn.adjust_date_time_to_timezone(
                xs.string("arg"),
                timezone=xs.string("timezone"),
            ),
            "fn:adjust-dateTime-to-timezone(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "timezone"},
            id="adjust_date_time_to_timezone",
        ),
        pytest.param(
            fn.adjust_time_to_timezone(
                xs.string("arg"),
                timezone=xs.string("timezone"),
            ),
            "fn:adjust-time-to-timezone(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "timezone"},
            id="adjust_time_to_timezone",
        ),
        pytest.param(
            fn.analyze_string(
                xs.string("in_"),
                xs.string("regex"),
                flags=xs.string("flags"),
            ),
            "fn:analyze-string(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "in_", "v1": "regex", "v2": "flags"},
            id="analyze_string",
        ),
        pytest.param(
            fn.avg(xs.string("arg")),
            "fn:avg(xs:string($v0))",
            {"v0": "arg"},
            id="avg",
        ),
        pytest.param(
            fn.base_uri(xs.string("arg")),
            "fn:base-uri(xs:string($v0))",
            {"v0": "arg"},
            id="base_uri",
        ),
        pytest.param(
            fn.boolean(xs.string("arg"), collation=xs.string("collation")),
            "fn:boolean(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "collation"},
            id="boolean",
        ),
        pytest.param(
            fn.ceiling(xs.string("arg")),
            "fn:ceiling(xs:string($v0))",
            {"v0": "arg"},
            id="ceiling",
        ),
        pytest.param(
            fn.codepoint_equal(xs.string("comparand1"), xs.string("comparand2")),
            "fn:codepoint-equal(xs:string($v0), xs:string($v1))",
            {"v0": "comparand1", "v1": "comparand2"},
            id="codepoint_equal",
        ),
        pytest.param(
            fn.codepoints_to_string(xs.string("arg")),
            "fn:codepoints-to-string(xs:string($v0))",
            {"v0": "arg"},
            id="codepoints_to_string",
        ),
        pytest.param(
            fn.collection(xs.string("uri")),
            "fn:collection(xs:string($v0))",
            {"v0": "uri"},
            id="collection",
        ),
        pytest.param(
            fn.compare(
                xs.string("comparand1"),
                xs.string("comparand2"),
                collation=xs.string("collation"),
            ),
            "fn:compare(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "comparand1", "v1": "comparand2", "v2": "collation"},
            id="compare",
        ),
        pytest.param(
            fn.concat(xs.string("parameter1"), xs.string("parameters")),
            "fn:concat(xs:string($v0), xs:string($v1))",
            {"v0": "parameter1", "v1": "parameters"},
            id="concat",
        ),
        pytest.param(
            fn.contains(
                xs.string("parameter1"),
                xs.string("parameter2"),
                collation=xs.string("collation"),
            ),
            "fn:contains(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "parameter1", "v1": "parameter2", "v2": "collation"},
            id="contains",
        ),
        pytest.param(
            fn.count(xs.string("sequence"), maximum=xs.string("maximum")),
            "fn:count(xs:string($v0), xs:string($v1))",
            {"v0": "sequence", "v1": "maximum"},
            id="count",
        ),
        pytest.param(fn.current(), "fn:current()", {}, id="current"),
        pytest.param(fn.current_date(), "fn:current-date()", {}, id="current_date"),
        pytest.param(
            fn.current_date_time(),
            "fn:current-dateTime()",
            {},
            id="current_date_time",
        ),
        pytest.param(fn.current_group(), "fn:current-group()", {}, id="current_group"),
        pytest.param(
            fn.current_grouping_key(),
            "fn:current-grouping-key()",
            {},
            id="current_grouping_key",
        ),
        pytest.param(fn.current_time(), "fn:current-time()", {}, id="current_time"),
        pytest.param(
            fn.data(xs.string("arg")),
            "fn:data(xs:string($v0))",
            {"v0": "arg"},
            id="data",
        ),
        pytest.param(
            fn.date_time(xs.string("arg1"), xs.string("arg2")),
            "fn:dateTime(xs:string($v0), xs:string($v1))",
            {"v0": "arg1", "v1": "arg2"},
            id="date_time",
        ),
        pytest.param(
            fn.day_from_date(xs.string("arg")),
            "fn:day-from-date(xs:string($v0))",
            {"v0": "arg"},
            id="day_from_date",
        ),
        pytest.param(
            fn.day_from_date_time(xs.string("arg")),
            "fn:day-from-dateTime(xs:string($v0))",
            {"v0": "arg"},
            id="day_from_date_time",
        ),
        pytest.param(
            fn.days_from_duration(xs.string("arg")),
            "fn:days-from-duration(xs:string($v0))",
            {"v0": "arg"},
            id="days_from_duration",
        ),
        pytest.param(
            fn.deep_equal(
                xs.string("parameter1"),
                xs.string("parameter2"),
                collation=xs.string("collation"),
            ),
            "fn:deep-equal(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "parameter1", "v1": "parameter2", "v2": "collation"},
            id="deep_equal",
        ),
        pytest.param(
            fn.default_collation(),
            "fn:default-collation()",
            {},
            id="default_collation",
        ),
        pytest.param(
            fn.distinct_nodes(xs.string("nodes")),
            "fn:distinct-nodes(xs:string($v0))",
            {"v0": "nodes"},
            id="distinct_nodes",
        ),
        pytest.param(
            fn.distinct_values(xs.string("arg"), collation=xs.string("collation")),
            "fn:distinct-values(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "collation"},
            id="distinct_values",
        ),
        pytest.param(
            fn.doc(xs.string("uri")),
            "fn:doc(xs:string($v0))",
            {"v0": "uri"},
            id="doc",
        ),
        pytest.param(
            fn.doc_available(xs.string("uri")),
            "fn:doc-available(xs:string($v0))",
            {"v0": "uri"},
            id="doc_available",
        ),
        pytest.param(
            fn.document(xs.string("uris"), base_node=xs.string("base_node")),
            "fn:document(xs:string($v0), xs:string($v1))",
            {"v0": "uris", "v1": "base_node"},
            id="document",
        ),
        pytest.param(
            fn.document_uri(xs.string("arg")),
            "fn:document-uri(xs:string($v0))",
            {"v0": "arg"},
            id="document_uri",
        ),
        pytest.param(
            fn.element_available(xs.string("element_name")),
            "fn:element-available(xs:string($v0))",
            {"v0": "element_name"},
            id="element_available",
        ),
        pytest.param(
            fn.empty(xs.string("sequence")),
            "fn:empty(xs:string($v0))",
            {"v0": "sequence"},
            id="empty",
        ),
        pytest.param(
            fn.encode_for_uri(xs.string("uri_part")),
            "fn:encode-for-uri(xs:string($v0))",
            {"v0": "uri_part"},
            id="encode_for_uri",
        ),
        pytest.param(
            fn.ends_with(
                xs.string("parameter1"),
                xs.string("parameter2"),
                collation=xs.string("collation"),
            ),
            "fn:ends-with(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "parameter1", "v1": "parameter2", "v2": "collation"},
            id="ends_with",
        ),
        pytest.param(
            fn.error(xs.string("error"), xs.string("description"), xs.string("data")),
            "fn:error(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "error", "v1": "description", "v2": "data"},
            id="error",
        ),
        pytest.param(
            fn.escape_html_uri(xs.string("uri_part")),
            "fn:escape-html-uri(xs:string($v0))",
            {"v0": "uri_part"},
            id="escape_html_uri",
        ),
        pytest.param(
            fn.escape_uri(xs.string("uri_part"), xs.string("escape_reserved")),
            "fn:escape-uri(xs:string($v0), xs:string($v1))",
            {"v0": "uri_part", "v1": "escape_reserved"},
            id="escape_uri",
        ),
        pytest.param(
            fn.exactly_one(xs.string("arg")),
            "fn:exactly-one(xs:string($v0))",
            {"v0": "arg"},
            id="exactly_one",
        ),
        pytest.param(
            fn.exists(xs.string("sequence")),
            "fn:exists(xs:string($v0))",
            {"v0": "sequence"},
            id="exists",
        ),
        pytest.param(
            fn.expanded_qname(xs.string("param_uri"), xs.string("param_local")),
            "fn:expanded-QName(xs:string($v0), xs:string($v1))",
            {"v0": "param_uri", "v1": "param_local"},
            id="expanded_qname",
        ),
        pytest.param(fn.false(), "fn:false()", {}, id="false"),
        pytest.param(
            fn.filter(xs.string("function"), xs.string("seq")),
            "fn:filter(xs:string($v0), xs:string($v1))",
            {"v0": "function", "v1": "seq"},
            id="filter",
        ),
        pytest.param(
            fn.floor(xs.string("arg")),
            "fn:floor(xs:string($v0))",
            {"v0": "arg"},
            id="floor",
        ),
        pytest.param(
            fn.fold_left(xs.string("function"), xs.string("zero"), xs.string("seq")),
            "fn:fold-left(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "function", "v1": "zero", "v2": "seq"},
            id="fold_left",
        ),
        pytest.param(
            fn.fold_right(xs.string("function"), xs.string("zero"), xs.string("seq")),
            "fn:fold-right(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "function", "v1": "zero", "v2": "seq"},
            id="fold_right",
        ),
        pytest.param(
            fn.format_date(
                xs.string("value"),
                xs.string("picture"),
                language=xs.string("language"),
                calendar=xs.string("calendar"),
                country=xs.string("country"),
            ),
            (
                "fn:format-date(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4))"
            ),
            {
                "v0": "value",
                "v1": "picture",
                "v2": "language",
                "v3": "calendar",
                "v4": "country",
            },
            id="format_date",
        ),
        pytest.param(
            fn.format_date_time(
                xs.string("value"),
                xs.string("picture"),
                language=xs.string("language"),
                calendar=xs.string("calendar"),
                country=xs.string("country"),
            ),
            (
                "fn:format-dateTime(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4))"
            ),
            {
                "v0": "value",
                "v1": "picture",
                "v2": "language",
                "v3": "calendar",
                "v4": "country",
            },
            id="format_date_time",
        ),
        pytest.param(
            fn.format_number(
                xs.string("value"),
                xs.string("picture"),
                decimal_format_name=xs.string("decimal_format_name"),
            ),
            "fn:format-number(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "value", "v1": "picture", "v2": "decimal_format_name"},
            id="format_number",
        ),
        pytest.param(
            fn.format_time(
                xs.string("value"),
                xs.string("picture"),
                language=xs.string("language"),
                calendar=xs.string("calendar"),
                country=xs.string("country"),
            ),
            (
                "fn:format-time(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4))"
            ),
            {
                "v0": "value",
                "v1": "picture",
                "v2": "language",
                "v3": "calendar",
                "v4": "country",
            },
            id="format_time",
        ),
        pytest.param(
            fn.function_arity(xs.string("function")),
            "fn:function-arity(xs:string($v0))",
            {"v0": "function"},
            id="function_arity",
        ),
        pytest.param(
            fn.function_available(xs.string("function_name"), arity=xs.string("arity")),
            "fn:function-available(xs:string($v0), xs:string($v1))",
            {"v0": "function_name", "v1": "arity"},
            id="function_available",
        ),
        pytest.param(
            fn.function_lookup(xs.string("name"), xs.string("arity")),
            "fn:function-lookup(xs:string($v0), xs:string($v1))",
            {"v0": "name", "v1": "arity"},
            id="function_lookup",
        ),
        pytest.param(
            fn.function_name(xs.string("function")),
            "fn:function-name(xs:string($v0))",
            {"v0": "function"},
            id="function_name",
        ),
        pytest.param(
            fn.generate_id(xs.string("node")),
            "fn:generate-id(xs:string($v0))",
            {"v0": "node"},
            id="generate_id",
        ),
        pytest.param(
            fn.head(xs.string("seq")),
            "fn:head(xs:string($v0))",
            {"v0": "seq"},
            id="head",
        ),
        pytest.param(
            fn.hours_from_date_time(xs.string("arg")),
            "fn:hours-from-dateTime(xs:string($v0))",
            {"v0": "arg"},
            id="hours_from_date_time",
        ),
        pytest.param(
            fn.hours_from_duration(xs.string("arg")),
            "fn:hours-from-duration(xs:string($v0))",
            {"v0": "arg"},
            id="hours_from_duration",
        ),
        pytest.param(
            fn.hours_from_time(xs.string("arg")),
            "fn:hours-from-time(xs:string($v0))",
            {"v0": "arg"},
            id="hours_from_time",
        ),
        pytest.param(
            fn.id(xs.string("arg"), node=xs.string("node")),
            "fn:id(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "node"},
            id="id",
        ),
        pytest.param(
            fn.idref(xs.string("arg"), node=xs.string("node")),
            "fn:idref(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "node"},
            id="idref",
        ),
        pytest.param(
            fn.implicit_timezone(),
            "fn:implicit-timezone()",
            {},
            id="implicit_timezone",
        ),
        pytest.param(
            fn.in_scope_prefixes(xs.string("element")),
            "fn:in-scope-prefixes(xs:string($v0))",
            {"v0": "element"},
            id="in_scope_prefixes",
        ),
        pytest.param(
            fn.index_of(
                xs.string("seq_param"),
                xs.string("srch_param"),
                collation_literal=xs.string("collation_literal"),
            ),
            "fn:index-of(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "seq_param", "v1": "srch_param", "v2": "collation_literal"},
            id="index_of",
        ),
        pytest.param(
            fn.insert_before(
                xs.string("target"),
                xs.string("position"),
                xs.string("inserts"),
            ),
            "fn:insert-before(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "target", "v1": "position", "v2": "inserts"},
            id="insert_before",
        ),
        pytest.param(
            fn.iri_to_uri(xs.string("uri_part")),
            "fn:iri-to-uri(xs:string($v0))",
            {"v0": "uri_part"},
            id="iri_to_uri",
        ),
        pytest.param(
            fn.key(xs.string("key_name"), xs.string("key_value"), top=xs.string("top")),
            "fn:key(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "key_name", "v1": "key_value", "v2": "top"},
            id="key",
        ),
        pytest.param(
            fn.lang(xs.string("testlang"), node=xs.string("node")),
            "fn:lang(xs:string($v0), xs:string($v1))",
            {"v0": "testlang", "v1": "node"},
            id="lang",
        ),
        pytest.param(fn.last(), "fn:last()", {}, id="last"),
        pytest.param(
            fn.local_name(xs.string("arg")),
            "fn:local-name(xs:string($v0))",
            {"v0": "arg"},
            id="local_name",
        ),
        pytest.param(
            fn.local_name_from_qname(xs.string("arg")),
            "fn:local-name-from-QName(xs:string($v0))",
            {"v0": "arg"},
            id="local_name_from_qname",
        ),
        pytest.param(
            fn.lower_case(xs.string("string")),
            "fn:lower-case(xs:string($v0))",
            {"v0": "string"},
            id="lower_case",
        ),
        pytest.param(
            fn.map(xs.string("function"), xs.string("seq")),
            "fn:map(xs:string($v0), xs:string($v1))",
            {"v0": "function", "v1": "seq"},
            id="map",
        ),
        pytest.param(
            fn.map_pairs(xs.string("function"), xs.string("seq1"), xs.string("seq2")),
            "fn:map-pairs(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "function", "v1": "seq1", "v2": "seq2"},
            id="map_pairs",
        ),
        pytest.param(
            fn.matches(
                xs.string("input"),
                xs.string("pattern"),
                flags=xs.string("flags"),
            ),
            "fn:matches(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "input", "v1": "pattern", "v2": "flags"},
            id="matches",
        ),
        pytest.param(
            fn.max(xs.string("arg"), collation=xs.string("collation")),
            "fn:max(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "collation"},
            id="max",
        ),
        pytest.param(
            fn.min(xs.string("arg"), collation=xs.string("collation")),
            "fn:min(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "collation"},
            id="min",
        ),
        pytest.param(
            fn.minutes_from_date_time(xs.string("arg")),
            "fn:minutes-from-dateTime(xs:string($v0))",
            {"v0": "arg"},
            id="minutes_from_date_time",
        ),
        pytest.param(
            fn.minutes_from_duration(xs.string("arg")),
            "fn:minutes-from-duration(xs:string($v0))",
            {"v0": "arg"},
            id="minutes_from_duration",
        ),
        pytest.param(
            fn.minutes_from_time(xs.string("arg")),
            "fn:minutes-from-time(xs:string($v0))",
            {"v0": "arg"},
            id="minutes_from_time",
        ),
        pytest.param(
            fn.month_from_date(xs.string("arg")),
            "fn:month-from-date(xs:string($v0))",
            {"v0": "arg"},
            id="month_from_date",
        ),
        pytest.param(
            fn.month_from_date_time(xs.string("arg")),
            "fn:month-from-dateTime(xs:string($v0))",
            {"v0": "arg"},
            id="month_from_date_time",
        ),
        pytest.param(
            fn.months_from_duration(xs.string("arg")),
            "fn:months-from-duration(xs:string($v0))",
            {"v0": "arg"},
            id="months_from_duration",
        ),
        pytest.param(
            fn.name(xs.string("arg")),
            "fn:name(xs:string($v0))",
            {"v0": "arg"},
            id="name",
        ),
        pytest.param(
            fn.namespace_uri(xs.string("arg")),
            "fn:namespace-uri(xs:string($v0))",
            {"v0": "arg"},
            id="namespace_uri",
        ),
        pytest.param(
            fn.namespace_uri_for_prefix(xs.string("prefix"), xs.string("element")),
            "fn:namespace-uri-for-prefix(xs:string($v0), xs:string($v1))",
            {"v0": "prefix", "v1": "element"},
            id="namespace_uri_for_prefix",
        ),
        pytest.param(
            fn.namespace_uri_from_qname(xs.string("arg")),
            "fn:namespace-uri-from-QName(xs:string($v0))",
            {"v0": "arg"},
            id="namespace_uri_from_qname",
        ),
        pytest.param(
            fn.nilled(xs.string("arg")),
            "fn:nilled(xs:string($v0))",
            {"v0": "arg"},
            id="nilled",
        ),
        pytest.param(
            fn.node_kind(xs.string("node")),
            "fn:node-kind(xs:string($v0))",
            {"v0": "node"},
            id="node_kind",
        ),
        pytest.param(
            fn.node_name(xs.string("arg")),
            "fn:node-name(xs:string($v0))",
            {"v0": "arg"},
            id="node_name",
        ),
        pytest.param(
            fn.normalize_space(xs.string("input")),
            "fn:normalize-space(xs:string($v0))",
            {"v0": "input"},
            id="normalize_space",
        ),
        pytest.param(
            fn.normalize_unicode(
                xs.string("arg"),
                normalization_form=xs.string("normalization_form"),
            ),
            "fn:normalize-unicode(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "normalization_form"},
            id="normalize_unicode",
        ),
        pytest.param(
            fn.not_(xs.string("arg")),
            "fn:not(xs:string($v0))",
            {"v0": "arg"},
            id="not_",
        ),
        pytest.param(
            fn.number(xs.string("arg")),
            "fn:number(xs:string($v0))",
            {"v0": "arg"},
            id="number",
        ),
        pytest.param(
            fn.one_or_more(xs.string("arg")),
            "fn:one-or-more(xs:string($v0))",
            {"v0": "arg"},
            id="one_or_more",
        ),
        pytest.param(fn.position(), "fn:position()", {}, id="position"),
        pytest.param(
            fn.prefix_from_qname(xs.string("arg")),
            "fn:prefix-from-QName(xs:string($v0))",
            {"v0": "arg"},
            id="prefix_from_qname",
        ),
        pytest.param(
            fn.qname(xs.string("uri"), xs.string("lexical")),
            "fn:QName(xs:string($v0), xs:string($v1))",
            {"v0": "uri", "v1": "lexical"},
            id="qname",
        ),
        pytest.param(
            fn.regex_group(xs.string("group_number")),
            "fn:regex-group(xs:string($v0))",
            {"v0": "group_number"},
            id="regex_group",
        ),
        pytest.param(
            fn.remove(xs.string("target"), xs.string("position")),
            "fn:remove(xs:string($v0), xs:string($v1))",
            {"v0": "target", "v1": "position"},
            id="remove",
        ),
        pytest.param(
            fn.replace(
                xs.string("input"),
                xs.string("pattern"),
                xs.string("replacement"),
                flags=xs.string("flags"),
            ),
            (
                "fn:replace(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "input", "v1": "pattern", "v2": "replacement", "v3": "flags"},
            id="replace",
        ),
        pytest.param(
            fn.resolve_qname(xs.string("qname"), xs.string("element")),
            "fn:resolve-QName(xs:string($v0), xs:string($v1))",
            {"v0": "qname", "v1": "element"},
            id="resolve_qname",
        ),
        pytest.param(
            fn.resolve_uri(xs.string("relative"), base=xs.string("base")),
            "fn:resolve-uri(xs:string($v0), xs:string($v1))",
            {"v0": "relative", "v1": "base"},
            id="resolve_uri",
        ),
        pytest.param(
            fn.reverse(xs.string("target")),
            "fn:reverse(xs:string($v0))",
            {"v0": "target"},
            id="reverse",
        ),
        pytest.param(
            fn.root(xs.string("arg")),
            "fn:root(xs:string($v0))",
            {"v0": "arg"},
            id="root",
        ),
        pytest.param(
            fn.round(xs.string("arg")),
            "fn:round(xs:string($v0))",
            {"v0": "arg"},
            id="round",
        ),
        pytest.param(
            fn.round_half_to_even(xs.string("arg"), precision=xs.string("precision")),
            "fn:round-half-to-even(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "precision"},
            id="round_half_to_even",
        ),
        pytest.param(
            fn.seconds_from_date_time(xs.string("arg")),
            "fn:seconds-from-dateTime(xs:string($v0))",
            {"v0": "arg"},
            id="seconds_from_date_time",
        ),
        pytest.param(
            fn.seconds_from_duration(xs.string("arg")),
            "fn:seconds-from-duration(xs:string($v0))",
            {"v0": "arg"},
            id="seconds_from_duration",
        ),
        pytest.param(
            fn.seconds_from_time(xs.string("arg")),
            "fn:seconds-from-time(xs:string($v0))",
            {"v0": "arg"},
            id="seconds_from_time",
        ),
        pytest.param(
            fn.starts_with(
                xs.string("parameter1"),
                xs.string("parameter2"),
                collation=xs.string("collation"),
            ),
            "fn:starts-with(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "parameter1", "v1": "parameter2", "v2": "collation"},
            id="starts_with",
        ),
        pytest.param(
            fn.static_base_uri(),
            "fn:static-base-uri()",
            {},
            id="static_base_uri",
        ),
        pytest.param(
            fn.string(xs.string("arg")),
            "fn:string(xs:string($v0))",
            {"v0": "arg"},
            id="string",
        ),
        pytest.param(
            fn.string_join(xs.string("parameter1"), xs.string("parameter2")),
            "fn:string-join(xs:string($v0), xs:string($v1))",
            {"v0": "parameter1", "v1": "parameter2"},
            id="string_join",
        ),
        pytest.param(
            fn.string_length(xs.string("source_string")),
            "fn:string-length(xs:string($v0))",
            {"v0": "source_string"},
            id="string_length",
        ),
        pytest.param(
            fn.string_pad(xs.string("pad_string"), xs.string("pad_count")),
            "fn:string-pad(xs:string($v0), xs:string($v1))",
            {"v0": "pad_string", "v1": "pad_count"},
            id="string_pad",
        ),
        pytest.param(
            fn.string_to_codepoints(xs.string("arg")),
            "fn:string-to-codepoints(xs:string($v0))",
            {"v0": "arg"},
            id="string_to_codepoints",
        ),
        pytest.param(
            fn.subsequence(
                xs.string("source_seq"),
                xs.string("starting_loc"),
                length=xs.string("length"),
            ),
            "fn:subsequence(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "source_seq", "v1": "starting_loc", "v2": "length"},
            id="subsequence",
        ),
        pytest.param(
            fn.substring(
                xs.string("source_string"),
                xs.string("starting_loc"),
                length=xs.string("length"),
            ),
            "fn:substring(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "source_string", "v1": "starting_loc", "v2": "length"},
            id="substring",
        ),
        pytest.param(
            fn.substring_after(
                xs.string("input"),
                xs.string("after"),
                collation=xs.string("collation"),
            ),
            "fn:substring-after(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "input", "v1": "after", "v2": "collation"},
            id="substring_after",
        ),
        pytest.param(
            fn.substring_before(
                xs.string("input"),
                xs.string("before"),
                collation=xs.string("collation"),
            ),
            "fn:substring-before(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "input", "v1": "before", "v2": "collation"},
            id="substring_before",
        ),
        pytest.param(
            fn.subtract_date_times_yielding_day_time_duration(
                xs.string("srcval1"),
                xs.string("srcval2"),
            ),
            (
                "fn:subtract-dateTimes-yielding-dayTimeDuration(xs:string($v0), "
                "xs:string($v1))"
            ),
            {"v0": "srcval1", "v1": "srcval2"},
            id="subtract_date_times_yielding_day_time_duration",
        ),
        pytest.param(
            fn.subtract_date_times_yielding_year_month_duration(
                xs.string("srcval1"),
                xs.string("srcval2"),
            ),
            (
                "fn:subtract-dateTimes-yielding-yearMonthDuration(xs:string($v0), "
                "xs:string($v1))"
            ),
            {"v0": "srcval1", "v1": "srcval2"},
            id="subtract_date_times_yielding_year_month_duration",
        ),
        pytest.param(
            fn.sum(xs.string("arg"), zero=xs.string("zero")),
            "fn:sum(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "zero"},
            id="sum",
        ),
        pytest.param(
            fn.system_property(xs.string("property_name")),
            "fn:system-property(xs:string($v0))",
            {"v0": "property_name"},
            id="system_property",
        ),
        pytest.param(
            fn.tail(xs.string("seq")),
            "fn:tail(xs:string($v0))",
            {"v0": "seq"},
            id="tail",
        ),
        pytest.param(
            fn.timezone_from_date(xs.string("arg")),
            "fn:timezone-from-date(xs:string($v0))",
            {"v0": "arg"},
            id="timezone_from_date",
        ),
        pytest.param(
            fn.timezone_from_date_time(xs.string("arg")),
            "fn:timezone-from-dateTime(xs:string($v0))",
            {"v0": "arg"},
            id="timezone_from_date_time",
        ),
        pytest.param(
            fn.timezone_from_time(xs.string("arg")),
            "fn:timezone-from-time(xs:string($v0))",
            {"v0": "arg"},
            id="timezone_from_time",
        ),
        pytest.param(
            fn.tokenize(
                xs.string("input"),
                xs.string("pattern"),
                flags=xs.string("flags"),
            ),
            "fn:tokenize(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "input", "v1": "pattern", "v2": "flags"},
            id="tokenize",
        ),
        pytest.param(
            fn.trace(xs.string("value"), xs.string("label")),
            "fn:trace(xs:string($v0), xs:string($v1))",
            {"v0": "value", "v1": "label"},
            id="trace",
        ),
        pytest.param(
            fn.translate(
                xs.string("src"),
                xs.string("map_string"),
                xs.string("trans_string"),
            ),
            "fn:translate(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "src", "v1": "map_string", "v2": "trans_string"},
            id="translate",
        ),
        pytest.param(fn.true(), "fn:true()", {}, id="true"),
        pytest.param(
            fn.type_available(xs.string("type_name")),
            "fn:type-available(xs:string($v0))",
            {"v0": "type_name"},
            id="type_available",
        ),
        pytest.param(
            fn.unordered(xs.string("source_seq")),
            "fn:unordered(xs:string($v0))",
            {"v0": "source_seq"},
            id="unordered",
        ),
        pytest.param(
            fn.unparsed_entity_public_id(xs.string("entity_name")),
            "fn:unparsed-entity-public-id(xs:string($v0))",
            {"v0": "entity_name"},
            id="unparsed_entity_public_id",
        ),
        pytest.param(
            fn.unparsed_entity_uri(xs.string("entity_name")),
            "fn:unparsed-entity-uri(xs:string($v0))",
            {"v0": "entity_name"},
            id="unparsed_entity_uri",
        ),
        pytest.param(
            fn.unparsed_text(xs.string("href"), encoding=xs.string("encoding")),
            "fn:unparsed-text(xs:string($v0), xs:string($v1))",
            {"v0": "href", "v1": "encoding"},
            id="unparsed_text",
        ),
        pytest.param(
            fn.unparsed_text_available(
                xs.string("href"),
                encoding=xs.string("encoding"),
            ),
            "fn:unparsed-text-available(xs:string($v0), xs:string($v1))",
            {"v0": "href", "v1": "encoding"},
            id="unparsed_text_available",
        ),
        pytest.param(
            fn.upper_case(xs.string("string")),
            "fn:upper-case(xs:string($v0))",
            {"v0": "string"},
            id="upper_case",
        ),
        pytest.param(
            fn.year_from_date(xs.string("arg")),
            "fn:year-from-date(xs:string($v0))",
            {"v0": "arg"},
            id="year_from_date",
        ),
        pytest.param(
            fn.year_from_date_time(xs.string("arg")),
            "fn:year-from-dateTime(xs:string($v0))",
            {"v0": "arg"},
            id="year_from_date_time",
        ),
        pytest.param(
            fn.years_from_duration(xs.string("arg")),
            "fn:years-from-duration(xs:string($v0))",
            {"v0": "arg"},
            id="years_from_duration",
        ),
        pytest.param(
            fn.zero_or_one(xs.string("arg")),
            "fn:zero-or-one(xs:string($v0))",
            {"v0": "arg"},
            id="zero_or_one",
        ),
    ],
)
def test_compile_native_call(expression, body, variables):
    declarations = "".join(
        f"declare variable ${key} as xs:string external;\n" for key in variables
    )
    assert expression.compile() == (
        'xquery version "1.0-ml";\n' + declarations + body,
        variables,
    )
