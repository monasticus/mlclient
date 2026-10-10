"""Native directory query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import DirectoryQuery, cts


def run():
    query = cts.directory_query(["/reports/", "/notes/"], depth="infinity")
    assert isinstance(query, DirectoryQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ndeclare variable $v2 as xs:string external;\ncts:dire"
            "ctory-query(($v0, $v1), xs:string($v2))"
        ),
        {"v0": "/reports/", "v1": "/notes/", "v2": "infinity"},
    )
