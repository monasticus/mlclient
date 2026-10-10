"""Native union query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import OrQuery, cts


def run():
    query = cts.or_query([cts.collection_query("reports")], options="synonym")
    assert isinstance(query, OrQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ncts:or-query((cts:collection-query($v0)), $v1)"
        ),
        {"v0": "reports", "v1": "synonym"},
    )
