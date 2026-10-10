"""Test structured-query composition through the public builder."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import sq


def run():
    query = sq.query(
        sq.and_(
            sq.range(sq.element("price"), 20, operator="GE", index_type="xs:int"),
            sq.term("blue"),
        ),
    )
    expected = ElementTree.fromstring(
        '<query xmlns="http://marklogic.com/appservices/search">'
        '<and-query><range-query type="xs:int"><element name="pr'
        'ice" ns="" /><value>20</value><range-operator>GE</range'
        "-operator></range-query><term-query><text>blue</text></"
        "term-query></and-query></query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
