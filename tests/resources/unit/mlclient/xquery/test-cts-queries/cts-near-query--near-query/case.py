"""Native proximity query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import NearQuery, cts


def run():
    query = cts.near_query(
        [cts.true_query(), cts.false_query()],
        distance=2.5,
        options=["ordered", "minimum-distance=2"],
        distance_weight=0.5,
    )
    assert isinstance(query, NearQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:dou'
            "ble external;\ndeclare variable $v1 as xs:string externa"
            "l;\ndeclare variable $v2 as xs:string external;\ndeclare "
            "variable $v3 as xs:double external;\ncts:near-query((cts"
            ":true-query(), cts:false-query()), $v0, ($v1, $v2), $v3"
            ")"
        ),
        {"v0": "2.5", "v1": "ordered", "v2": "minimum-distance=2", "v3": "0.5"},
    )
