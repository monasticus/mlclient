"""Native directory query serialization and compilation."""

from xml.etree.ElementTree import tostring

import pytest

from mlclient.xquery import DirectoryQuery, cts, xs


def test_directory_query():
    query = cts.directory_query(["/reports/", "/notes/"], depth="infinity")
    assert isinstance(query, DirectoryQuery)
    assert query.serialize() == {
        "directoryQuery": {"uris": ["/reports/", "/notes/"], "depth": "infinity"},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:directory-query xmlns:cts="http://marklogic.com/cts" depth="infin'
        'ity">'
        "<cts:uri>/reports/</cts:uri>"
        "<cts:uri>/notes/</cts:uri>"
        "</cts:directory-query>"
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "declare variable $v1 as xs:string external;\n"
            "declare variable $v2 as xs:string external;\n"
            "cts:directory-query(($v0, $v1), xs:string($v2))"
        ),
        {"v0": "/reports/", "v1": "/notes/", "v2": "infinity"},
    )


def test_directory_query_default_depth():
    query = cts.directory_query("/reports/")
    assert query.serialize() == {"directoryQuery": {"uris": ["/reports/"]}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:directory-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:uri>/reports/</cts:uri></cts:directory-query>"
    )


def test_directory_query_empty():
    assert cts.directory_query([]).serialize() == {"directoryQuery": {}}


def test_directory_query_invalid_local_depth_expression():
    with pytest.raises(
        ValueError,
        match="must be '1' or 'infinity'",
    ) as exc:
        DirectoryQuery("/reports/", xs.string("2")).serialize()
    assert str(exc.value) == (
        "cts:directory-query: depth ['2'] must be '1' or 'infinity'"
    )
