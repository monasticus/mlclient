"""Native json property scope query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import JsonPropertyScopeQuery, cts


def run():
    query = cts.json_property_scope_query(["report", "note"], cts.true_query())
    assert isinstance(query, JsonPropertyScopeQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ncts:json-property-scope-query(($v0, $v1), cts:true-q"
            "uery())"
        ),
        {"v0": "report", "v1": "note"},
    )
