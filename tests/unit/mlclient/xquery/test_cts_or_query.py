"""Native union query serialization and compilation."""

from xml.etree.ElementTree import tostring

import pytest

from mlclient.xquery import OrQuery, cts


def test_or_query():
    query = cts.or_query([cts.collection_query("reports")], options="synonym")
    assert isinstance(query, OrQuery)
    assert query.serialize() == {
        "orQuery": {
            "queries": [{"collectionQuery": {"uris": ["reports"]}}],
            "options": ["synonym"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:or-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query>"
        "<cts:option>synonym</cts:option></cts:or-query>"
    )
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "cts:or-query((cts:collection-query($v0)), $v1)",
        {"v0": "reports", "v1": "synonym"},
    )


def test_or_query_empty():
    assert cts.or_query([]).serialize() == {"orQuery": {}}


def test_or_query_unsupported_options():
    with pytest.raises(
        ValueError,
        match="are not or-query options",
    ) as exc:
        cts.or_query([], options="ordered")
    assert str(exc.value) == (
        "options ['ordered'] are not or-query options; use at most one of synonym"
    )


def test_or_query_duplicate_options():
    with pytest.raises(
        ValueError,
        match="are not or-query options",
    ) as exc:
        cts.or_query([], options=["synonym", "synonym"])
    assert str(exc.value) == (
        "options ['synonym', 'synonym'] are not or-query options; "
        "use at most one of synonym"
    )
