"""Public compilation and native serialization of RangeQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import cts, fn


def run():
    query = cts.range_query(
        [
            cts.element_attribute_reference(
                fn.qname("urn:reports", "report"),
                "label",
                options=[
                    "type=string",
                    "collation=http://marklogic.com/collation/",
                    "nullable",
                ],
            ),
            cts.field_reference("price", options=["type=int", "non-nullable"]),
            cts.json_property_reference("price", options="type=int"),
            cts.path_reference("/report/price", options="type=int"),
            cts.uri_reference(),
            cts.collection_reference(),
            cts.iri_reference(),
        ],
        "=",
        "blue",
    )
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-1.xml",
    )
