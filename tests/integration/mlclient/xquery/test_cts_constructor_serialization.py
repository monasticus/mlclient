"""Check that MarkLogic reconstructs selector, range, geospatial and temporal CTS
queries from both local serializations exactly as the native constructors build them.

Queries are compared through their native JSON form: XML QName prefixes may
differ from the constructor's while naming the same QNames.
"""

import datetime
import json
import os
from decimal import Decimal
from xml.etree.ElementTree import ElementTree, fromstring, tostring

import pytest

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.xquery import FunctionCall, cts, fn, xdmp, xs

pytestmark = pytest.mark.ml_access

NS = "urn:mlclient:cts-test"
START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
END = datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc)
POINT = cts.point(10.5, -20.25)

QUERIES = {
    "after": cts.after_query(16000000000),
    "before": cts.before_query(16000000000),
    "element": cts.element_query(["a", fn.qname(NS, "t:b")], cts.word_query("x")),
    "element-word": cts.element_word_query(
        fn.qname(NS, "title"),
        ["blue", "red"],
        options="case-insensitive",
        weight=2,
    ),
    "element-value": cts.element_value_query("title", "blue"),
    "element-value-any": cts.element_value_query("title"),
    "element-attribute-value": cts.element_attribute_value_query(
        "item",
        "status",
        "ok",
        options="exact",
        weight=0.5,
    ),
    "element-attribute-word": cts.element_attribute_word_query("item", "status", "ok"),
    "element-range-integer": cts.element_range_query(
        "price",
        ">=",
        10,
        options="min-occurs=1",
        weight=2,
    ),
    "element-range-decimal": cts.element_range_query("price", "<", Decimal("1.5")),
    "element-range-double": cts.element_range_query("price", ">", xs.double(1.5)),
    "element-range-strings": cts.element_range_query("code", "=", ["a", "b"]),
    "element-range-date": cts.element_range_query(
        "day",
        ">",
        datetime.date(2026, 1, 1),
    ),
    "element-range-date-time": cts.element_range_query("at", "<=", START),
    "element-range-boolean": cts.element_range_query("flag", "=", True),
    "element-attribute-range": cts.element_attribute_range_query(
        "item",
        "amount",
        "!=",
        3,
    ),
    "field-value": cts.field_value_query("", ["1", "2"], weight=3),
    "field-range": cts.field_range_query("price", "<=", 2),
    "json-property-value-string": cts.json_property_value_query("label", "gamma"),
    "json-property-value-number": cts.json_property_value_query("count", 7),
    "json-property-value-boolean": cts.json_property_value_query("active", True),
    "json-property-value-mixed": cts.json_property_value_query(
        ["a", "b"],
        ["x", 1.5, False],
    ),
    "json-property-range": cts.json_property_range_query("price", ">", 10),
    "path-range": cts.path_range_query("/item/price", ">", 1),
    "element-geospatial-point": cts.element_geospatial_query(
        "origin",
        POINT,
        options="coordinate-system=wgs84",
        weight=2,
    ),
    "element-geospatial-regions": cts.element_geospatial_query(
        "origin",
        [
            cts.box(1.5, 2, 3, 4),
            cts.circle(5, cts.point(10, 20)),
            cts.polygon(
                [cts.point(0, 0), cts.point(0, 1), cts.point(1, 1), cts.point(0, 0)],
            ),
        ],
    ),
    "element-child-geospatial": cts.element_child_geospatial_query(
        "location",
        "point",
        POINT,
    ),
    "element-pair-geospatial": cts.element_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        POINT,
    ),
    "element-attribute-pair-geospatial": cts.element_attribute_pair_geospatial_query(
        "item",
        "lat",
        "lon",
        POINT,
        weight=3,
    ),
    "json-property-geospatial": cts.json_property_geospatial_query("origin", POINT),
    "json-property-child-geospatial": cts.json_property_child_geospatial_query(
        "location",
        "point",
        POINT,
    ),
    "json-property-pair-geospatial": cts.json_property_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        POINT,
    ),
    "path-geospatial": cts.path_geospatial_query("/item/origin", POINT),
    "period-compare": cts.period_compare_query(
        "system",
        "aln_equals",
        "valid",
        options="cached-incremental",
    ),
    "period-range": cts.period_range_query(
        ["valid", "system"],
        "aln_before",
        period=cts.period(START, END),
    ),
    "lsqt": cts.lsqt_query("temporal", timestamp=START, options="cached", weight=2),
    "registered": cts.registered_query([1, 2], options="unfiltered", weight=2),
    "range-reference": cts.range_query(
        [
            cts.element_reference("price", options=["type=int", "unchecked"]),
            cts.json_property_reference("price", options=["type=int", "unchecked"]),
        ],
        "=",
        [2, 3],
        options="cached",
        weight=2,
    ),
    "region-reference": cts.geospatial_region_query(
        cts.geospatial_region_path_reference(
            "/report/region",
            options=["unchecked", "coordinate-system=wgs84"],
            geohash_precision=4,
            units="km",
            invalid_values="reject",
        ),
        "intersects",
        cts.box(1, 2, 3, 4),
        weight=2,
    ),
    "triple": cts.triple_range_query(
        FunctionCall("sem:iri", ("urn:report:1",)),
        FunctionCall("sem:iri", ("urn:label",)),
        [2, True, "blue"],
        operator=">",
        options="cached",
        weight=2,
    ),
    "reverse-json": cts.reverse_query(
        xdmp.unquote('{"label":"blue","count":2}'),
        weight=2,
    ),
    "geo-box-fractional": cts.element_geospatial_query(
        "location",
        cts.box(10.1, 20.2, 30.3, 40.4),
    ),
    "not": cts.not_query(cts.word_query("blue")),
    "json-property-scope": cts.json_property_scope_query(
        ["report", "summary"],
        cts.word_query("blue"),
    ),
    "properties-fragment": cts.properties_fragment_query(cts.word_query("blue")),
    "locks-fragment": cts.locks_fragment_query(cts.word_query("blue")),
    "document-fragment": cts.document_fragment_query(cts.word_query("blue")),
    "element-attribute-word-options": cts.element_attribute_word_query(
        "item",
        "status",
        ["ok", "done"],
        options=["case-insensitive", "stemmed"],
        weight=2,
    ),
    "namespaced-attribute": cts.element_attribute_value_query(
        fn.qname(NS, "t:item"),
        fn.qname(NS, "t:status"),
        "ok",
    ),
    "composed-operators": (
        cts.word_query("blue") | cts.word_query("red")
    ) & ~cts.collection_query("archive"),
}

ML11_QUERIES = {
    "document-format": cts.document_format_query("json"),
    "document-permission": cts.document_permission_query("admin", "read"),
    "document-root-unqualified": cts.document_root_query("root"),
}


class TestCtsConstructorSerialization:
    @pytest.fixture(scope="class")
    @staticmethod
    def ml_client():
        with MLClient(port=int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))) as ml:
            yield ml

    @pytest.mark.parametrize("name", QUERIES)
    def test_reconstruction(self, ml_client, name):
        self.assert_reconstructed(ml_client, QUERIES[name])

    @pytest.mark.parametrize("name", ML11_QUERIES)
    def test_reconstruction_on_marklogic_11(self, ml_client, name):
        if ml_client.version.parts[0] < 11:
            pytest.skip("requires MarkLogic 11+")
        self.assert_reconstructed(ml_client, ML11_QUERIES[name])

    def test_namespaced_document_root_reconstructs_from_json_only(self, ml_client):
        # MarkLogic cannot read a namespaced root QName back from XML, even from
        # the constructor's own XML, so only the JSON form round-trips.
        if ml_client.version.parts[0] < 11:
            pytest.skip("requires MarkLogic 11+")
        query = cts.document_root_query(fn.qname(NS, "t:root"))
        code, variables = query.compile()
        lines = code.splitlines(keepends=True)
        boundary = next(
            index for index, line in enumerate(lines)
            if not line.startswith(("xquery version", "declare variable"))
        )
        prolog, body = "".join(lines[:boundary]), "".join(lines[boundary:])
        variables["serialized_json"] = json.dumps(query.to_json())
        native, from_json = ml_client.eval.xquery(
            prolog + "\ndeclare variable $serialized_json as xs:string external;\n"
            "let $native := " + body + "\n"
            "return ("
            "xdmp:quote(xdmp:to-json($native)), "
            "xdmp:quote(xdmp:to-json(cts:query(xdmp:unquote($serialized_json)/node()))))",
            variables=variables,
        )
        assert from_json == native
        with pytest.raises(MarkLogicError, match="XDMP-CAST"):
            ml_client.eval.xquery(
                prolog + "\ncts:query(<a>{" + body + "}</a>/*)",
                variables=variables,
            )

    def test_element_attribute_reference_reconstructs_from_xml_only(self, ml_client):
        # MarkLogic cannot read an element-attribute reference back from its own
        # JSON form (XDMP-RANGEINDEXNODE), so JSON serialization rejects it.
        query = cts.range_query(
            cts.element_attribute_reference(
                "item",
                "amount",
                options=["type=int", "unchecked"],
            ),
            "=",
            2,
        )
        code, variables = query.compile()
        lines = code.splitlines(keepends=True)
        boundary = next(
            index for index, line in enumerate(lines)
            if not line.startswith(("xquery version", "declare variable"))
        )
        prolog, body = "".join(lines[:boundary]), "".join(lines[boundary:])
        variables["serialized_xml"] = tostring(query.to_xml(), encoding="unicode")
        native, from_xml = ml_client.eval.xquery(
            prolog + "\ndeclare variable $serialized_xml as xs:string external;\n"
            "let $native := " + body + "\n"
            "return ("
            "xdmp:quote(xdmp:to-json($native)), "
            "xdmp:quote(xdmp:to-json(cts:query(xdmp:unquote($serialized_xml)/*))))",
            variables=variables,
        )
        assert from_xml == native
        with pytest.raises(MarkLogicError, match="XDMP-RANGEINDEXNODE"):
            ml_client.eval.xquery(
                prolog + "\ncts:query(xdmp:to-json(" + body + ")/node())",
                variables=variables,
            )
        with pytest.raises(TypeError, match="element-attribute reference"):
            query.to_json()

    def test_reverse_xml_model_nodes(self, ml_client):
        query = cts.reverse_query(
            FunctionCall(
                "xdmp:unquote",
                ('<report xmlns:r="urn:reports"><r:label>blue</r:label></report>',),
            ).xpath("*"),
            weight=2,
        )
        self.assert_model_nodes(ml_client, query, "reverse")

    def test_similar_xml_model_nodes_and_options(self, ml_client):
        query = cts.similar_query(
            FunctionCall("xdmp:unquote", ("<report>blue</report>",)).xpath("*"),
            options=FunctionCall(
                "xdmp:unquote",
                (
                    '<options xmlns="cts:distinctive-terms"><max-terms>20</max-terms>'
                    "<score>logtf</score><min-val>1</min-val><min-weight>2</min-weight>"
                    "<complete>true</complete></options>",
                ),
            ).xpath("*"),
            weight=2,
        )
        self.assert_model_nodes(ml_client, query, "similar")

    def test_python_node_inputs(self, ml_client):
        price = fromstring('<price xmlns="urn:prices">42</price>')
        assert ml_client.eval.expression(fn.local_name(price)) == "price"
        assert ml_client.eval.expression(xs.integer(price)) == 42
        assert ml_client.eval.expression(fn.local_name(fn.root(price))) == ""
        assert ml_client.eval.expression(fn.local_name(ElementTree(price))) == ""
        assert ml_client.eval.expression(fn.count([price, ElementTree(price)])) == 2
        model = {"label": "blue", "nested": [{"count": 2}]}
        assert ml_client.eval.expression(fn.head(model)) == model
        assert ml_client.eval.expression(
            xdmp.unquote(fromstring("<text>&lt;report/&gt;</text>")),
        ).getroot().tag == "report"
        query = cts.similar_query(
            price,
            options=fromstring(
                '<options xmlns="cts:distinctive-terms"><max-terms>20</max-terms>'
                '</options>',
            ),
        )
        self.assert_model_nodes(ml_client, query, "similar")

    def test_unquote_parsing_options_and_default_namespace(self, ml_client):
        root = ml_client.eval.expression(
            xdmp.unquote(
                "<report/>", default_namespace="urn:reports", options="repair-none",
            ).xpath("*"),
        )
        assert root.tag == "{urn:reports}report"
        assert ml_client.eval.expression(
            xdmp.unquote('{"label":"blue"}', options="format-json"),
        ) == {"label": "blue"}

    def test_similar_json_model_has_the_native_xml_reader_limitation(self, ml_client):
        query = cts.similar_query(
            {"label": "blue", "count": 2},
        )
        code, variables = query.compile()
        lines = code.splitlines(keepends=True)
        boundary = next(
            index for index, line in enumerate(lines)
            if not line.startswith(("xquery version", "declare variable"))
        )
        prolog, body = "".join(lines[:boundary]), "".join(lines[boundary:])
        variables.update(
            xml=tostring(query.to_xml(), encoding="unicode"),
            json=json.dumps(query.to_json()),
        )
        results = ml_client.eval.xquery(
            prolog + "\ndeclare variable $xml external;"
            "declare variable $json external;\n"
            "let $native := " + body + "\nreturn array-node {\n"
            "xdmp:to-json(cts:query(<a>{$native}</a>/*))/node(), "
            "xdmp:to-json(cts:query(xdmp:unquote($xml)/*))/node(), "
            "xdmp:to-json(cts:query(xdmp:unquote($json)/node()))/node()}",
            variables=variables,
        )
        assert results == [
            {"similarQuery": {"nodes": ['{"label":"blue", "count":2}']}},
            {"similarQuery": {"nodes": ['{"label":"blue", "count":2}']}},
            {"similarQuery": {"nodes": [{"label": "blue", "count": 2}]}},
        ]

    @staticmethod
    def assert_model_nodes(ml_client, query, kind):
        code, variables = query.compile()
        lines = code.splitlines(keepends=True)
        boundary = next(
            index
            for index, line in enumerate(lines)
            if not line.startswith(("xquery version", "declare variable"))
        )
        prolog, body = "".join(lines[:boundary]), "".join(lines[boundary:])
        variables.update(
            xml=tostring(query.to_xml(), encoding="unicode"),
            json=json.dumps(query.to_json()),
        )
        result = ml_client.eval.xquery(
            prolog + "declare variable $xml external;declare variable $json external;\n"
            "let $native := (" + body + ")\n"
            "let $xml := cts:query(xdmp:unquote($xml)/*)\n"
            "let $json := cts:query(xdmp:unquote($json)/node())\n"
            "return object-node {\n"
            '"xmlNodes": fn:deep-equal(cts:' + kind + "-query-nodes($native), "
            "cts:" + kind + "-query-nodes($xml)),\n"
            '"jsonNodes": fn:deep-equal(cts:' + kind + "-query-nodes($native), "
            "cts:" + kind + "-query-nodes($json)),\n"
            '"native": xdmp:to-json($native)/node(), '
            '"xml": xdmp:to-json($xml)/node(), "json": xdmp:to-json($json)/node()}',
            variables=variables,
        )
        assert result["xmlNodes"] is True
        assert result["jsonNodes"] is True
        for representation in ("native", "xml", "json"):
            result[representation][kind + "Query"].pop("nodes")
        assert result["native"] == result["xml"] == result["json"]

    @staticmethod
    def assert_reconstructed(ml_client, query):
        code, variables = query.compile()
        lines = code.splitlines(keepends=True)
        boundary = next(
            index for index, line in enumerate(lines)
            if not line.startswith(("xquery version", "declare variable"))
        )
        prolog, body = "".join(lines[:boundary]), "".join(lines[boundary:])
        variables["serialized_xml"] = tostring(query.to_xml(), encoding="unicode")
        variables["serialized_json"] = json.dumps(query.to_json())
        native, from_xml, from_json = ml_client.eval.xquery(
            prolog + "\ndeclare variable $serialized_xml as xs:string external;\n"
            "declare variable $serialized_json as xs:string external;\n"
            "let $native := " + body + "\n"
            "return ("
            "xdmp:quote(xdmp:to-json($native)), "
            "xdmp:quote(xdmp:to-json(cts:query(xdmp:unquote($serialized_xml)/*))), "
            "xdmp:quote(xdmp:to-json(cts:query(xdmp:unquote($serialized_json)/node()))))",
            variables=variables,
        )
        assert from_xml == native
        assert from_json == native
