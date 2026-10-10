"""Check that MarkLogic reads both CTS serializations as the native constructor."""

from tests.utils.resources import render_test_resource

import json
import os
from xml.etree.ElementTree import tostring

import pytest

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.xquery import cts, xdmp

pytestmark = pytest.mark.ml_access


class TestCtsQuerySerialization:
    @pytest.fixture(scope="class")
    @staticmethod
    def ml_client():
        with MLClient(port=int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))) as ml:
            yield ml

    def test_runtime_parse(self, ml_client):
        query = cts.parse("blue AND green")
        document = xdmp.unquote("<report>blue green</report>")
        assert ml_client.eval.expression(cts.contains(document, query)) is True
        document = xdmp.unquote("<report>blue</report>")
        assert ml_client.eval.expression(cts.contains(document, query)) is False

    def test_runtime_query(self, ml_client):
        source = json.dumps(cts.word_query("blue", options="lang=en").to_json())
        query = cts.query(xdmp.unquote(source).xpath("node()"))
        document = xdmp.unquote("<report>blue</report>")
        assert ml_client.eval.expression(cts.contains(document, query)) is True
        document = xdmp.unquote("<report>green</report>")
        assert ml_client.eval.expression(cts.contains(document, query)) is False

    def test_word_query(self, ml_client):
        self.assert_native(ml_client, cts.word_query("blue", options="lang=en"))

    def test_word_query_exact(self, ml_client):
        self.assert_native(
            ml_client,
            cts.word_query(
                ["blue", "green"],
                options=["lang=FR", "exact"],
                weight=2,
            ),
        )

    def test_word_query_without_language(self, ml_client):
        self.assert_native(ml_client, cts.word_query("blue"))

    def test_word_query_unordered_options(self, ml_client):
        self.assert_native(
            ml_client,
            cts.word_query(
                "blue",
                options=["unstemmed", "case-insensitive", "lang=fr"],
            ),
        )

    def test_word_query_empty(self, ml_client):
        self.assert_native(ml_client, cts.word_query(None, options="lang=en", weight=1))

    def test_word_query_out_of_range_weight(self, ml_client):
        self.assert_native(
            ml_client,
            cts.word_query("blue", options="lang=en", weight=100),
        )

    def test_word_query_small_weight(self, ml_client):
        self.assert_native(
            ml_client,
            cts.word_query("blue", options="lang=en", weight=0.00001),
        )

    def test_word_query_scientific_weight(self, ml_client):
        self.assert_native(
            ml_client,
            cts.word_query("blue", options="lang=en", weight=0.0000001),
        )

    def test_collection_query(self, ml_client):
        self.assert_native(ml_client, cts.collection_query(["reports", "notes"]))

    def test_collection_query_empty(self, ml_client):
        self.assert_native(ml_client, cts.collection_query([]))

    def test_and_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.and_query(
                [
                    cts.word_query("blue", options="lang=fr"),
                    cts.collection_query("reports"),
                ],
                options="ordered",
            ),
        )

    def test_and_query_implicit_words(self, ml_client):
        self.assert_native(ml_client, cts.and_query(["blue"]))

    def test_and_query_empty(self, ml_client):
        self.assert_native(ml_client, cts.and_query([]))

    def test_and_not_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.and_not_query(
                cts.collection_query("reports"),
                cts.collection_query("notes"),
            ),
        )

    def test_boost_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.boost_query(
                cts.collection_query("reports"),
                cts.collection_query("notes"),
            ),
        )

    def test_not_in_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.not_in_query(
                cts.collection_query("reports"),
                cts.collection_query("notes"),
            ),
        )

    def test_not_query(self, ml_client):
        self.assert_native(ml_client, cts.not_query(cts.collection_query("reports")))

    def test_document_fragment_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.document_fragment_query(cts.collection_query("reports")),
        )

    def test_locks_fragment_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.locks_fragment_query(cts.collection_query("reports")),
        )

    def test_properties_fragment_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.properties_fragment_query(cts.collection_query("reports")),
        )

    def test_document_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.document_query(["/reports/a.xml", "/notes/b.json"]),
        )

    def test_false_query(self, ml_client):
        self.assert_native(ml_client, cts.false_query())

    def test_true_query(self, ml_client):
        self.assert_native(ml_client, cts.true_query())

    def test_or_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.or_query([cts.collection_query("reports")], options="synonym"),
        )

    def test_or_query_empty(self, ml_client):
        self.assert_native(ml_client, cts.or_query([]))

    def test_directory_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.directory_query(["/reports/", "/notes/"], depth="infinity"),
        )

    def test_json_property_scope_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.json_property_scope_query(["report", "note"], cts.true_query()),
        )

    def test_json_property_word_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.json_property_word_query(
                ["title", "body"],
                ["blue", "green"],
                options=["lang=en", "exact"],
                weight=2,
            ),
        )

    def test_field_word_query_default_field(self, ml_client):
        self.assert_native(
            ml_client,
            cts.field_word_query("", "blue", options="lang=en", weight=2),
        )

    def test_near_query(self, ml_client):
        self.assert_native(
            ml_client,
            cts.near_query(
                [cts.true_query(), cts.false_query()],
                distance=2.5,
                options=["ordered", "minimum-distance=2"],
                distance_weight=0.5,
            ),
        )

    def test_near_query_defaults(self, ml_client):
        self.assert_native(ml_client, cts.near_query([]))

    def test_near_query_negative_distance(self, ml_client):
        self.assert_native(ml_client, cts.near_query([], distance=-1))

    def test_near_query_large_distance(self, ml_client):
        # Native constructors emit this value, but cts:query rejects it as XML.
        with pytest.raises(MarkLogicError, match="XDMP-QUERYATTRVAL"):
            self.assert_native(ml_client, cts.near_query([], distance=1000000000000))

    def test_near_query_negative_minimum(self, ml_client):
        self.assert_native(ml_client, cts.near_query([], options="minimum-distance=-2"))

    def test_near_query_large_minimum(self, ml_client):
        with pytest.raises(MarkLogicError, match="XDMP-QUERYATTRVAL"):
            self.assert_native(
                ml_client,
                cts.near_query([], options="minimum-distance=4294967296"),
            )

    def test_directory_query_defaults(self, ml_client):
        self.assert_native(ml_client, cts.directory_query("/reports/"))

    @staticmethod
    def assert_native(ml_client, query):
        code, variables = query.compile()
        prolog, body = code.rsplit("\n", 1)
        variables["serialized_xml"] = tostring(query.to_xml(), encoding="unicode")
        variables["serialized_json"] = json.dumps(query.to_json())
        assert (
            ml_client.eval.xquery(
                render_test_resource(
                    __file__,
                    "assert-native.xqy",
                    prolog=prolog,
                    body=body,
                ),
                variables=variables,
            )
            is True
        )
