from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from mlclient.exceptions import MarkLogicError
from mlclient.functions.xqy import fn, xdmp, xpath, xs
from mlclient.models import BinaryDocument, JSONDocument, TextDocument
from mlclient.services import CtsService
from tests.utils.expressions import StaticExpression

pytestmark = pytest.mark.ml_access


class TestCtsService:
    def test_value_tuples_keep_single_json_array_inside_result_list(
        self,
        indexed_database,
    ):
        ml, database, _ = indexed_database
        cts = CtsService(ml.rest)
        assert cts.value_tuples(
            cts.uri_reference(),
            query=cts.document_query("/cts-test/a.xml"),
            database=database,
        ) == [["/cts-test/a.xml"]]

    def test_xml_search_scope_server_xpath_and_local_xpath(self, indexed_database):
        ml, database, _ = indexed_database
        uri = "/cts-test/catalog.xml"
        try:
            ml.eval.xquery(
                'xdmp:document-insert("/cts-test/catalog.xml", '
                '<catalog xmlns="https://monasticus.com/mlclient/examples/products">'
                "<product><title>Coffee beans</title><price>12</price></product>"
                "<product><title>Tea leaves</title><price>8</price></product>"
                "</catalog>)",
                database=database,
            )
            cts = CtsService(
                ml.rest,
                namespaces={"p": "https://monasticus.com/mlclient/examples/products"},
            )
            query = cts.word_query("coffee")
            [whole] = cts.search(query=query, database=database)
            assert (
                len(
                    whole.xpath(
                        "p:product",
                        p="https://monasticus.com/mlclient/examples/products",
                    ),
                )
                == 2
            )

            [product] = cts.search(
                expression="/p:catalog/p:product",
                query=query,
                database=database,
            )
            assert (
                product.xpath(
                    "p:title",
                    p="https://monasticus.com/mlclient/examples/products",
                )[0].text
                == "Coffee beans"
            )
            assert (
                product.xpath(
                    "p:price",
                    p="https://monasticus.com/mlclient/examples/products",
                )[0].text
                == "12"
            )
            assert len(product.content) == 2

            [title] = cts.search(
                expression="/p:catalog/p:product",
                query=query,
                xpath="p:title",
                database=database,
            )
            assert title.content.text == "Coffee beans"
            assert (
                title.xpath(
                    "p:price",
                    p="https://monasticus.com/mlclient/examples/products",
                )
                == []
            )
            assert title.score == product.score
        finally:
            ml.documents.delete(uri, database=database)

    def test_mixed_content_and_scalar_nodes_preserve_types_and_scores(
        self,
        indexed_database,
    ):
        (ml, database, _) = indexed_database
        uris = ["/cts-types/text.txt", "/cts-types/binary.bin", "/cts-types/json.json"]
        binary = b"\x00\xffA\r\n\x00"
        try:
            ml.documents.write(
                [
                    TextDocument("abcd", uri=uris[0]),
                    BinaryDocument(binary, uri=uris[1]),
                    JSONDocument(
                        {"a": "b", "n": 123, "f": False, "z": None, "arr": [1, 2]},
                        uri=uris[2],
                    ),
                ],
                database=database,
            )
            cts = CtsService(ml.rest)
            query = cts.document_query([*uris, "/cts-test/a.xml"])
            hits = cts.search(query=query, database=database)
            by_uri = {hit.source_uri: hit for hit in hits}
            assert all(isinstance(hit.score, int) for hit in hits)
            assert by_uri[uris[0]].content == "abcd"
            assert by_uri[uris[1]].content == binary
            assert by_uri[uris[2]].content["a"] == "b"
            assert by_uri[uris[2]].source_path == "/"
            assert (
                by_uri["/cts-test/a.xml"].content.getroot().tag
                == "{https://monasticus.com/mlclient/examples/cts-test}item"
            )
            for node_path, expected in [
                ('text("a")', "b"),
                ('number-node("n")', 123),
                ('boolean-node("f")', False),
                ('null-node("z")', None),
                ('array-node("arr")', [1, 2]),
            ]:
                [hit] = cts.search(
                    query=cts.document_query(uris[2]),
                    xpath=node_path,
                    database=database,
                )
                assert hit.content == expected
                assert type(hit.content) is type(expected)
                assert hit.source_uri == uris[2]
                assert hit.source_path == "/" + node_path
                assert isinstance(hit.score, int)
        finally:
            ml.documents.delete(uris, database=database)

    def test_field_values_aggregates_and_map_boundary(self, indexed_database):
        (ml, database, _) = indexed_database
        cts = CtsService(ml.rest)
        collection = cts.collections(database=database)
        assert collection[0].value == "cts-test"
        assert collection[0].frequency == 3
        assert cts.collection_match("cts-*", database=database) == collection
        assert cts.uri_match("/cts-test/*.xml", database=database) == [
            "/cts-test/a.xml",
            "/cts-test/b.xml",
        ]
        values = cts.field_values("price", database=database)
        assert [value.value for value in values] == [Decimal("1.25"), Decimal("2.50")]
        assert [value.frequency for value in values] == [1, 1]
        assert cts.field_values("price", index=1, database=database)[
            0
        ].value == Decimal(
            "1.25",
        )
        assert (
            cts.field_values("price", query=cts.false_query(), database=database) == []
        )
        assert cts.sum_aggregate(
            cts.field_reference("price"),
            database=database,
        ) == [Decimal("3.75")]
        assert ml.eval.expression(cts.field_values("price"), database=database) == [
            Decimal("1.25"),
            Decimal("2.50"),
        ]
        with pytest.raises(ValueError, match="Map output"):
            cts.values(cts.uri_reference(), options="map", database=database)
        with pytest.raises(MarkLogicError, match="MLCLIENT-LEXICON-MAP"):
            cts.values(cts.uri_reference(), options=xs.string("map"), database=database)

    def test_xpath_retains_original_positive_score(self, indexed_database):
        ml, database, _ = indexed_database
        cts = CtsService(
            ml.rest,
            namespaces={"p": "https://monasticus.com/mlclient/examples/cts-test"},
        )
        query = cts.word_query("alpha")
        [original] = cts.search(query=query, index=1, database=database)
        [selected] = cts.search(
            query=query,
            index=1,
            xpath="p:item/p:label",
            database=database,
        )
        assert original.score > 0
        assert selected.score == original.score
        assert selected.content.text == "alpha"
        assert selected.source_uri == original.source_uri
        assert selected.source_path != original.source_path

    def test_result_xpath_pairs_multiple_nodes_with_the_original_score(
        self,
        indexed_database,
    ):
        ml, database, _ = indexed_database
        cts = CtsService(
            ml.rest,
            namespaces={"p": "https://monasticus.com/mlclient/examples/cts-test"},
        )
        query = cts.word_query("alpha")
        [original] = cts.search(query=query, index=1, database=database)

        selected = cts.search(
            query=query,
            index=1,
            xpath="p:item/*",
            database=database,
        )

        assert [hit.content.text for hit in selected] == [
            "1.25",
            "2026-01-01",
            "alpha",
            "10,20",
            "30,40",
        ]
        assert original.score > 0
        assert all(hit.score == original.score for hit in selected)
        assert all(hit.source_uri == original.source_uri for hit in selected)

    def test_search_xpath_preserves_order_and_selects_hits_first(
        self,
        indexed_database,
    ):
        ml, database, _ = indexed_database
        cts = CtsService(
            ml.rest,
            namespaces={"p": "https://monasticus.com/mlclient/examples/cts-test"},
        )
        options = cts.index_order(
            cts.element_reference(
                fn.qname("https://monasticus.com/mlclient/examples/cts-test", "price"),
            ),
            options="descending",
        )
        parameters = {"expression": "/p:item", "options": options, "database": database}
        labels = cts.search(**parameters, xpath="p:label")
        assert [label.content.text for label in labels] == ["beta", "alpha"]
        assert (
            cts.search(**parameters, index=2, xpath="p:label")[0].content.text
            == "alpha"
        )
        assert (
            cts.search(**parameters, range=[2, 2], xpath="p:label")[0].content.text
            == "alpha"
        )
        children = cts.search(**parameters, index=1, xpath="*")
        assert [child.content.text for child in children] == [
            "2.50",
            "2026-01-02",
            "beta",
        ]
        assert cts.search(**parameters, index=100, xpath="p:label") == []
        assert cts.search(**parameters, xpath="p:absent") == []
        assert (
            cts.search(**parameters, index=1, xpath="/p:item/p:label")[0].content.text
            == "beta"
        )
        assert (
            cts.search(
                options=options,
                database=database,
                index=1,
                xpath="p:item/p:label",
            )[0].content.text
            == "beta"
        )
        with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH"):
            cts.search(**parameters, xpath="p:label), fn:error() (: ")

    def test_search_lexicons_ranges_and_namespace_composition(self, indexed_database):
        ml, database, _ = indexed_database
        cts = CtsService(ml.rest)
        query = cts.and_query(
            [
                cts.collection_query("cts-test"),
                cts.element_range_query(
                    fn.qname(
                        "https://monasticus.com/mlclient/examples/cts-test",
                        "price",
                    ),
                    ">=",
                    Decimal("1.25"),
                ),
                cts.element_range_query(
                    fn.qname(
                        "https://monasticus.com/mlclient/examples/cts-test",
                        "day",
                    ),
                    ">=",
                    date(2026, 1, 1),
                ),
            ],
        )
        hits = cts.search(
            xpath("/Q{https://monasticus.com/mlclient/examples/cts-test}item"),
            query,
            options="filtered",
        )
        assert ml.eval.expression(fn.count(hits), database=database) == 2
        assert ml.eval.expression(fn.count(hits.range(2, 2)), database=database) == 1
        assert ml.eval.expression(xdmp.exists(hits), database=database) is True
        assert (
            ml.eval.expression(
                xdmp.exists(
                    xpath(
                        "/Q{https://monasticus.com/mlclient/examples/cts-test}absent",
                    ),
                ),
                database=database,
            )
            is False
        )
        assert cts.search(query=cts.false_query(), database=database) == []
        assert (
            cts.search(query=query, range=1, database=database)[0].content.getroot().tag
            == "{https://monasticus.com/mlclient/examples/cts-test}item"
        )
        assert cts.uris(query=query, database=database) == [
            "/cts-test/a.xml",
            "/cts-test/b.xml",
        ]
        assert cts.uris(query=query, start="/cts-test/b.xml", database=database) == [
            "/cts-test/b.xml",
        ]
        ref = cts.element_reference(
            fn.qname("https://monasticus.com/mlclient/examples/cts-test", "price"),
        )
        values = cts.values(ref)
        assert ml.eval.expression(fn.count(values), database=database) == 2
        assert ml.eval.expression(fn.exists(values), database=database) is True
        assert [
            hit.value for hit in cts.values(ref, query=query, database=database)
        ] == [
            Decimal("1.25"),
            Decimal("2.50"),
        ]
        assert cts.values(
            ref,
            query=query,
            start=Decimal(2),
            database=database,
        )[0].value == Decimal("2.50")
        assert cts.estimate(query, database=database) == [2]
        assert cts.estimate(query, maximum=1, database=database) == [1]
        assert cts.estimate(database=database) == [3]
        assert ml.eval.expression(cts.estimate(), database=database) == 3
        assert cts.search(
            query=cts.json_property_value_query("active", True),
            database=database,
        )[0].content == {"active": True}
        assert (
            ml.eval.expression(
                fn.count(cts.search(query=query), maximum=1),
                database=database,
            )
            == 1
        )
        assert ml.eval.expression(
            cts.word_query("alpha", weight=xs.double(fn.count([1]))),
            database=database,
        )
        forests = StaticExpression("xdmp:database-forests(xdmp:database())")
        assert cts.uris(
            query=query,
            quality_weight=0,
            forest_ids=forests,
            database=database,
        ) == ["/cts-test/a.xml", "/cts-test/b.xml"]

        path_ref = cts.path_reference(
            "/p:item/p:price",
            namespaces=StaticExpression(
                'map:map() => map:with("p", "https://monasticus.com/mlclient/examples/cts-test")',
            ),
        )
        assert [
            hit.value for hit in cts.values(path_ref, query=query, database=database)
        ] == [
            Decimal("1.25"),
            Decimal("2.50"),
        ]
        assert cts.estimate(
            cts.path_range_query(
                "/Q{https://monasticus.com/mlclient/examples/cts-test}item/Q{https://monasticus.com/mlclient/examples/cts-test}price",
                ">",
                Decimal(2),
            ),
            database=database,
        ) == [1]
        assert (
            cts.search(
                query=cts.word_query(
                    "(: (( :) /), cts:false-query()), 424242, (( (: )) :)",
                ),
                database=database,
            )
            == []
        )

    def test_all_paths_are_guarded_with_shared_and_local_namespaces(
        self,
        indexed_database,
    ):
        ml, database, _ = indexed_database
        bindings = {
            "p": "https://monasticus.com/mlclient/examples/cts-test",
            "other": "https://monasticus.com/mlclient/examples/absent",
        }
        cts = CtsService(ml.rest, namespaces=bindings)
        bindings["p"] = "https://monasticus.com/mlclient/examples/mutated"
        assert len(cts.search("/p:item", database=database)) == 2
        assert (
            cts.search(
                "/p:item",
                namespaces={"p": "https://monasticus.com/mlclient/examples/absent"},
                database=database,
            )
            == []
        )
        assert len(cts.search("/p:item", database=database)) == 2
        assert (
            len(
                cts.search(
                    "/item",
                    namespaces={
                        "": "https://monasticus.com/mlclient/examples/cts-test",
                    },
                    database=database,
                ),
            )
            == 2
        )
        paths = [cts.search("/p:item"), cts.search("/other:item")]
        assert (
            ml.eval.expression(
                fn.count(paths),
                namespaces={
                    "p": "https://monasticus.com/mlclient/examples/cts-test",
                    "other": "https://monasticus.com/mlclient/examples/absent",
                },
                database=database,
            )
            == 2
        )
        assert (
            ml.eval.expression(
                cts.valid_extract_path("/p:item"),
                namespaces={"p": "https://monasticus.com/mlclient/examples/cts-test"},
                database=database,
            )
            is True
        )
        assert (
            ml.eval.expression(
                cts.valid_index_path("/p:item/p:price", False),
                namespaces={"p": "https://monasticus.com/mlclient/examples/cts-test"},
                database=database,
            )
            is True
        )
        default_service = CtsService(
            ml.rest,
            namespaces={"": "https://monasticus.com/mlclient/examples/cts-test"},
        )
        assert len(default_service.search("/item", database=database)) == 2
        assert (
            default_service.search(
                "/item",
                namespaces={"": ""},
                database=database,
            )
            == []
        )
        uri = (
            'https://monasticus.com/mlclient/examples/test"; '
            'fn:error(xs:QName("INJECTED")); (: &'
        )
        assert (
            ml.eval.expression(
                StaticExpression('fn:namespace-uri-from-QName(xs:QName("p:x"))'),
                namespaces={"p": uri},
                output_type=str,
                database=database,
            )
            == uri
        )
        reference_bindings = {"p": "https://monasticus.com/mlclient/examples/cts-test"}
        reference = cts.path_reference("/p:item/p:price", namespaces=reference_bindings)
        reference_bindings["p"] = "https://monasticus.com/mlclient/examples/mutated"
        assert [
            hit.value
            for hit in cts.values(
                reference,
                namespaces={"p": "https://monasticus.com/mlclient/examples/absent"},
                database=database,
            )
        ] == [Decimal("1.25"), Decimal("2.50")]
        assert cts.estimate(
            cts.path_range_query(["/p:item/p:price", "/p:item/p:price"], ">", 1),
            database=database,
        ) == [2]
        assert (
            ml.eval.expression(
                fn.count(
                    cts.search(
                        '/*[fn:node-name(.) => fn:string() => fn:contains("item")]',
                    ),
                ),
                database=database,
            )
            == 2
        )

    def test_position_context_and_service_index(self, indexed_database):
        ml, database, _ = indexed_database
        expression = StaticExpression("(10, 20, 30)")
        for position, expected in [(1, 10), (fn.last(), 30), (4, [])]:
            assert ml.eval.expression(expression.index(position)) == expected
        assert ml.eval.expression(expression.range(2, fn.last())) == [20, 30]
        assert ml.eval.expression(expression.range(fn.last(), fn.last())) == 30
        assert ml.eval.expression(expression.range(4, fn.last())) == []
        cts = CtsService(ml.rest)
        uris = cts.uris(database=database)
        assert cts.uris(index=1, database=database) == [uris[0]]
        assert cts.uris(index=fn.last(), database=database) == [uris[-1]]
        assert cts.uris(index=100, database=database) == []
        assert cts.uris(range=[2, fn.last()], database=database) == uris[1:]
