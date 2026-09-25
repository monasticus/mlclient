from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from docs.examples.custom_expression import label
from mlclient.exceptions import MarkLogicError
from mlclient.functions.xqy import Cts, ModuleFunctionCall, cts, fn, xpath, xs
from mlclient.models import TextDocument
from tests.utils.expressions import StaticExpression

pytestmark = pytest.mark.ml_access


class TestEvalService:
    @pytest.mark.parametrize(
        ("start", "end", "expected"),
        [
            (2, 3, ["c", "b"]),
            (2, fn.last(), ["c", "b", "a"]),
            (fn.last(), fn.last(), "a"),
        ],
    )
    def test_range_predicates_support_integer_bounds_and_last(
        self,
        indexed_database,
        start,
        end,
        expected,
    ):
        ml, database, _ = indexed_database
        expression = fn.reverse(["a", "b", "c", "d"]).range(start, end)

        assert ml.eval.expression(expression, database=database) == expected

    @pytest.mark.parametrize(
        "expression",
        [
            xpath("/t:item/t:label").index(1),
            xpath("/t:item/t:label").range(1, 1),
            cts.search("/t:item").xpath("t:label").index(1),
            cts.search("/t:item").xpath("t:label").range(1, 1),
        ],
    )
    def test_position_predicates_select_from_the_complete_sequence(
        self,
        indexed_database,
        expression,
    ):
        ml, database, _ = indexed_database
        assert (
            ml.eval.expression(
                fn.count(expression),
                namespaces={"t": "https://monasticus.com/mlclient/examples/cts-test"},
                database=database,
            )
            == 1
        )

    def test_count_distinguishes_a_string_from_a_validated_path(self, indexed_database):
        ml, database, _ = indexed_database
        assert ml.eval.expression(fn.count("/t:item"), database=database) == 1
        assert (
            ml.eval.expression(
                fn.count(xpath("/t:item")),
                namespaces={"t": "https://monasticus.com/mlclient/examples/cts-test"},
                database=database,
            )
            == 2
        )

    @pytest.mark.parametrize(
        "source",
        [
            "/[",
            "/unknown:item",
            'fn:error(fn:QName("", "SHOULD-NOT-RUN"))',
            '/) else "BYPASS", let $invalid-paths := () '
            "return if (fn:true()) then fn:count(/",
        ],
    )
    @pytest.mark.parametrize("nested", [False, True])
    def test_xpath_validation_cannot_be_bypassed(
        self,
        indexed_database,
        source,
        nested,
    ):
        ml, database, _ = indexed_database
        expression = xpath(source)
        if nested:
            expression = fn.count(expression)
        with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH") as error:
            ml.eval.expression(expression, database=database)
        assert "[xpath:v0]" in str(error.value)
        assert source in str(error.value)

    @pytest.mark.parametrize(
        ("direction", "expected"),
        [("ascending", ["alpha", "beta"]), ("descending", ["beta", "alpha"])],
    )
    def test_project_preserves_index_order_after_range(
        self,
        indexed_database,
        direction,
        expected,
    ):
        ml, database, _ = indexed_database
        expression = (
            cts.search(
                expression="/t:item",
                options=cts.index_order(
                    cts.element_reference(
                        fn.qname(
                            "https://monasticus.com/mlclient/examples/cts-test",
                            "price",
                        ),
                    ),
                    options=direction,
                ),
            )
            .range(1, 2)
            .xpath("t:label")
        )

        result = ml.eval.expression(
            expression,
            namespaces={"t": "https://monasticus.com/mlclient/examples/cts-test"},
            database=database,
        )

        assert [element.text for element in result] == expected

    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            (label.normalize("  coffee   beans  "), "COFFEE BEANS"),
            (label.join("coffee", "beans"), "coffee beans"),
            (label.join("coffee", "beans", separator=None), "coffee beans"),
            (label.join("coffee", "beans", separator="-"), "coffee-beans"),
            (label.join("coffee", "beans", separator=""), "coffeebeans"),
            (label.join(label.normalize(" coffee "), "beans"), "COFFEE beans"),
            (fn.string_length(label.normalize("  coffee  ")), 6),
            (label.normalize(label.normalize("  nested  ")), "NESTED"),
            (
                ModuleFunctionCall(
                    "normalize",
                    (label.normalize("  MiXeD  "),),
                    namespace="https://monasticus.com/mlclient/examples/other-labels",
                    module_path="/ext/example/other-labels.xqy",
                ),
                "mixed",
            ),
            (
                label.normalize(
                    fn.string(
                        cts.search(
                            expression="/t:item/t:label",
                            query=cts.word_query("alpha"),
                        ),
                    ),
                ),
                "ALPHA",
            ),
        ],
    )
    def test_custom_module_recipe_loads_its_namespace_and_composes(
        self,
        indexed_database,
        expression,
        expected,
    ):
        ml, database, _ = indexed_database
        module_uri = "/ext/example/labels.xqy"
        other_uri = "/ext/example/other-labels.xqy"
        module = Path("docs/examples/labels.xqy").read_text()
        other_module = module.replace(
            "https://monasticus.com/mlclient/examples/labels",
            "https://monasticus.com/mlclient/examples/other-labels",
        ).replace("fn:upper-case", "fn:lower-case")
        code, variables = expression.compile(
            namespaces={
                "t": "https://monasticus.com/mlclient/examples/cts-test",
                "label": "https://monasticus.com/mlclient/examples/unrelated",
            },
        )
        try:
            ml.documents.write(
                [
                    TextDocument(module, uri=module_uri),
                    TextDocument(other_module, uri=other_uri),
                ],
                database=database,
            )
            # Use the isolated database for modules without changing the App Server.
            result = ml.eval.xquery(
                "declare variable $code external; "
                "declare variable $bindings external; "
                "xdmp:eval($code, "
                "xdmp:from-json(xdmp:unquote($bindings)/object-node()), "
                '<options xmlns="xdmp:eval">'
                "<modules>{xdmp:database()}</modules><root>/</root></options>)",
                variables={"code": code, "bindings": json.dumps(variables)},
                database=database,
            )
            assert result == expected
        finally:
            ml.documents.delete([module_uri, other_uri], database=database)

    def test_scalar_roundtrips_and_sequence_composition(self, indexed_database):
        ml, database, _ = indexed_database

        def evaluate(expr):
            return ml.eval.expression(expr, database=database)

        assert evaluate(fn.count([1, 2])) == 2
        assert evaluate(fn.exists([])) is False
        assert evaluate(fn.empty(None)) is True
        assert evaluate(xs.integer(2**60 + 1)) == 2**60 + 1
        with pytest.raises(MarkLogicError, match="XDMP-AS"):
            evaluate(xs.integer(2**80))
        assert evaluate(xs.decimal(Decimal("1.234567890123456789"))) == Decimal(
            "1.234567890123456789",
        )
        assert evaluate(xs.date(date(2026, 1, 2))) == date(2026, 1, 2)
        stamp = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        assert evaluate(xs.date_time(stamp)) == stamp
        assert evaluate(xs.double(float("inf"))) == float("inf")
        assert math.isnan(evaluate(xs.double(float("nan"))))
        assert evaluate(xs.string(fn.count([1, 2]))) == "2"
        assert evaluate(StaticExpression("array-node {1,2}")) == [1, 2]
        assert evaluate(StaticExpression('"line 1\n  line 2"')) == "line 1\n  line 2"
        assert evaluate(fn.count([None, [], [1, 2]])) == 2

    def test_native_version_support_is_reported_by_server(self, indexed_database):
        ml, database, _ = indexed_database
        major = int(ml.eval.xquery("xdmp:version()").split(".")[0])
        expr = Cts.search(
            query=Cts.document_root_query(
                fn.qname("https://monasticus.com/mlclient/examples/cts-test", "item"),
            ),
        )
        if major < 11:
            with pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
                ml.eval.expression(expr, database=database)
        else:
            assert len(ml.eval.expression(expr, database=database)) == 2
        for native in (
            Cts.document_format_query("xml"),
            Cts.document_permission_query("admin", "read"),
            Cts.iri_reference(),
        ):
            if major < 11:
                with pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
                    ml.eval.expression(native, database=database)
            else:
                assert ml.eval.expression(fn.count(native), database=database) == 1

    def test_geospatial_and_triple_native_contracts(self, indexed_database):
        ml, database, _ = indexed_database
        pairs = Cts.geospatial_co_occurrences(
            fn.qname("https://monasticus.com/mlclient/examples/cts-test", "origin"),
            fn.qname(
                "https://monasticus.com/mlclient/examples/cts-test",
                "destination",
            ),
        )
        result = ml.eval.expression(pairs, database=database)
        assert result.tag == "{http://marklogic.com/cts}co-occurrence"
        assert ml.eval.expression(fn.count(pairs), database=database) == 1
        for operator in ("sameTerm", ["=", "=", "<"], []):
            query = Cts.triple_range_query([], [], 1, operator=operator)
            assert ml.eval.expression(fn.count(query), database=database) == 1

    def test_text_callbacks_and_native_maps(self, indexed_database):
        ml, database, _ = indexed_database
        node = StaticExpression("<p>alpha beta</p>")
        query = Cts.parse("alpha")
        result = ml.eval.expression(
            Cts.highlight(node, query, StaticExpression("<b>{$cts:text}</b>")),
            database=database,
        )
        assert result.find("b").text == "alpha"
        assert (
            ml.eval.expression(
                Cts.walk(node, query, StaticExpression("$cts:text")),
                database=database,
            )
            == "alpha"
        )
        assert (
            ml.eval.expression(
                Cts.contains(
                    node,
                    Cts.parse("alpha", bindings=StaticExpression("map:map()")),
                ),
                database=database,
            )
            is True
        )

    def test_extended_cts_catalog_executes_through_the_common_evaluator(
        self,
        indexed_database,
    ):
        ml, database, _ = indexed_database
        query = Cts.collection_query("cts-test")
        price = Cts.element_reference(
            fn.qname("https://monasticus.com/mlclient/examples/cts-test", "price"),
        )

        assert (
            ml.eval.expression(Cts.contains(StaticExpression("<p>alpha</p>"), query))
            is False
        )
        assert (
            ml.eval.expression(Cts.collections(query=query), database=database)
            == "cts-test"
        )
        assert (
            ml.eval.expression(
                Cts.collection_match("cts-*", query=query),
                database=database,
            )
            == "cts-test"
        )
        assert ml.eval.expression(
            Cts.uri_match("/cts-test/*.xml", query=query),
            database=database,
        ) == ["/cts-test/a.xml", "/cts-test/b.xml"]
        assert ml.eval.expression(
            Cts.min(price, query=query),
            database=database,
        ) == Decimal("1.25")
        assert ml.eval.expression(
            Cts.max(price, query=query),
            database=database,
        ) == Decimal("2.50")
        assert (
            ml.eval.expression(
                Cts.count_aggregate(price, query=query),
                database=database,
            )
            == 2
        )

        query_id = ml.eval.expression(Cts.register(query), database=database)
        try:
            assert isinstance(query_id, int)
            assert (
                ml.eval.expression(
                    Cts.estimate(Cts.registered_query(query_id)),
                    database=database,
                )
                == 3
            )
        finally:
            ml.eval.expression(Cts.deregister(query_id), database=database)

    def test_all_invalid_paths_reported_before_executing_tree(self, indexed_database):
        ml, database, _ = indexed_database
        bad_paths = [
            '/*[fn:doc("/not-executed")]',
            '/*, ()) else "INJECTED", if (true()) then cts:search(/*',
            "/unknown:price",
            '/p:item/p:price[xdmp:version() = "10"]',
        ]
        expression = fn.count(
            [
                Cts.search(bad_paths[0]),
                Cts.search(bad_paths[1]),
                fn.count(xpath(bad_paths[2])),
                xpath(bad_paths[3]),
                StaticExpression('fn:error(xs:QName("SHOULD-NOT-RUN"))'),
            ],
        )
        with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH") as error:
            ml.eval.expression(
                expression,
                namespaces={"p": "https://monasticus.com/mlclient/examples/cts-test"},
                database=database,
            )
        for path in bad_paths:
            assert path in str(error.value)
        assert "SHOULD-NOT-RUN" not in str(error.value)

    def test_decimal_parsing_and_qname_constructors(self, indexed_database):
        ml, database, _ = indexed_database
        expected = Decimal("0.1234567890123456789")
        assert ml.eval.xquery('xs:decimal("0.1234567890123456789")') == expected
        assert ml.eval.expression(xs.decimal(expected)) == expected
        names = {"p": "https://monasticus.com/mlclient/examples/cts-test"}
        assert (
            ml.eval.expression(
                xs.string(xs.qname("p:item")),
                namespaces=names,
            )
            == "p:item"
        )
        assert (
            ml.eval.expression(
                xs.string(
                    fn.qname(
                        "https://monasticus.com/mlclient/examples/cts-test",
                        "p:item",
                    ),
                ),
            )
            == "p:item"
        )
        assert (
            ml.eval.expression(
                fn.count(
                    Cts.search(
                        query=Cts.element_query(xs.qname("item"), Cts.true_query()),
                    ),
                ),
                namespaces={"": "https://monasticus.com/mlclient/examples/cts-test"},
                database=database,
            )
            == 2
        )

    @pytest.mark.parametrize(
        "expression",
        [
            Cts.geospatial_path_reference("/unknown:path"),
            Cts.geospatial_region_path_reference("/unknown:path"),
            Cts.path_geospatial_query("/unknown:path", Cts.point(10, 20)),
            Cts.path_range_query("/unknown:path", "=", 1),
            Cts.path_reference("/unknown:path"),
        ],
    )
    def test_string_path_arguments_are_validated_by_the_native_function(
        self,
        indexed_database,
        expression,
    ):
        ml, database, _ = indexed_database
        with pytest.raises(MarkLogicError) as error:
            ml.eval.expression(expression, database=database)
        assert "MLCLIENT-INVALID-PATH" not in str(error.value)

    def test_fn_catalog_representative_native_execution(self, indexed_database):
        ml, database, _ = indexed_database
        assert ml.eval.expression(fn.concat("a", None, "b", "c")) == "abc"
        assert ml.eval.expression(fn.substring("MarkLogic", 5, length=5)) == "Logic"
        assert ml.eval.expression(fn.tokenize("a,b,c", ",")) == ["a", "b", "c"]
        total = ml.eval.expression(fn.sum([Decimal("0.1"), Decimal("0.2")]))
        assert total == Decimal("0.3")
        assert ml.eval.expression(fn.subsequence([10, 20, 30, 40], 2, length=2)) == [
            20,
            30,
        ]
        assert ml.eval.expression(fn.head([])) == []
        assert ml.eval.expression(fn.tail([1, 2, 3])) == [2, 3]
        assert ml.eval.expression(fn.string(None)) == ""
        assert ml.eval.expression(fn.count(fn.collection()), database=database) == 3
        assert ml.eval.expression(fn.collection(None), database=database) == []
        upper = fn.function_lookup(
            fn.qname("http://www.w3.org/2005/xpath-functions", "upper-case"),
            1,
        )
        assert ml.eval.expression(fn.function_arity(upper)) == 1
        assert ml.eval.expression(fn.map(upper, ["a", "b"])) == ["A", "B"]
        assert ml.eval.expression(
            fn.filter(
                StaticExpression("function($x) { $x gt 1 }"),
                [1, 2, 3],
            ),
        ) == [2, 3]
        assert (
            ml.eval.expression(
                fn.fold_left(
                    StaticExpression("function($sum, $x) { $sum + $x }"),
                    0,
                    [1, 2, 3],
                ),
            )
            == 6
        )
        assert (
            ml.eval.expression(
                fn.adjust_date_to_timezone(
                    StaticExpression('xs:date("2026-01-02+02:00")'),
                    timezone=None,
                ),
                output_type=str,
            )
            == "2026-01-02"
        )
        with pytest.raises(MarkLogicError, match="FN-TEST"):
            ml.eval.expression(
                fn.error(
                    fn.qname("", "FN-TEST"),
                    description="expected test error",
                ),
            )
