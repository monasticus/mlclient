"""Native proximity query serialization and compilation."""

from xml.etree.ElementTree import tostring

import pytest

from mlclient.xquery import NearQuery, cts


def test_near_query():
    query = cts.near_query(
        [cts.true_query(), cts.false_query()],
        distance=2.5,
        options=["ordered", "minimum-distance=2"],
        distance_weight=0.5,
    )
    assert isinstance(query, NearQuery)
    assert query.serialize() == {
        "nearQuery": {
            "queries": [{"trueQuery": {}}, {"falseQuery": {}}],
            "distance": 3,
            "minimum-distance": 2,
            "options": ["ordered"],
            "weight": 0.5,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:near-query xmlns:cts="http://marklogic.com/cts" '
        'weight="0.5" distance="3" minimum-distance="2">'
        "<cts:true-query /><cts:false-query />"
        "<cts:option>ordered</cts:option></cts:near-query>"
    )
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:double external;\n"
        "declare variable $v1 as xs:string external;\n"
        "declare variable $v2 as xs:string external;\n"
        "declare variable $v3 as xs:double external;\n"
        "cts:near-query((cts:true-query(), cts:false-query()), "
        "$v0, ($v1, $v2), $v3)",
        {"v0": "2.5", "v1": "ordered", "v2": "minimum-distance=2", "v3": "0.5"},
    )


def test_near_query_default_distance():
    query = cts.near_query([])
    assert query.serialize() == {"nearQuery": {"distance": 10}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:near-query xmlns:cts="http://marklogic.com/cts" distance="10" />'
    )


def test_near_query_negative_distance():
    assert cts.near_query([], distance=-1).serialize() == {"nearQuery": {"distance": 0}}


def test_near_query_large_distance():
    assert cts.near_query([], distance=1000000000000).serialize() == {
        "nearQuery": {"distance": 3567587328},
    }


def test_near_query_negative_minimum():
    assert cts.near_query([], options="minimum-distance=-2").serialize() == {
        "nearQuery": {"distance": 10},
    }


def test_near_query_large_minimum():
    assert cts.near_query([], options="minimum-distance=4294967296").serialize() == {
        "nearQuery": {"distance": 10, "minimum-distance": 4294967295},
    }


def test_near_query_unsupported_options():
    with pytest.raises(
        ValueError,
        match="is not a near-query option",
    ) as exc:
        cts.near_query([], options="synonym")
    assert str(exc.value) == "option 'synonym' is not a near-query option"


def test_near_query_fractional_minimum():
    with pytest.raises(
        ValueError,
        match="is not a near-query option",
    ) as exc:
        cts.near_query([], options="minimum-distance=1.5")
    assert str(exc.value) == (
        "option 'minimum-distance=1.5' is not a near-query option"
    )


def test_near_query_conflicting_ordering():
    with pytest.raises(
        ValueError,
        match="repeat ordering or minimum-distance",
    ) as exc:
        cts.near_query([], options=["ordered", "unordered"])
    assert str(exc.value) == (
        "options ['ordered', 'unordered'] repeat ordering or minimum-distance"
    )


def test_near_query_duplicate_minimum():
    with pytest.raises(
        ValueError,
        match="repeat ordering or minimum-distance",
    ) as exc:
        cts.near_query(
            [],
            options=["minimum-distance=1", "minimum-distance=2"],
        )
    assert str(exc.value) == (
        "options ['minimum-distance=1', 'minimum-distance=2'] "
        "repeat ordering or minimum-distance"
    )
