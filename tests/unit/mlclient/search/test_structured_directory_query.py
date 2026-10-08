"""Test DirectoryQuery through the public structured-query API."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import DirectoryQuery


def test_directory_query_serializes_to_json():
    query = DirectoryQuery(["/reports/", "/notes/"], infinite=False)
    expected = {"directory-query": {"uri": ["/reports/", "/notes/"], "infinite": False}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_directory_query_serializes_to_xml():
    query = DirectoryQuery(["/reports/", "/notes/"], infinite=False)
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<directory-query>"
        "<uri>/reports/</uri>"
        "<uri>/notes/</uri>"
        "<infinite>false</infinite>"
        "</directory-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_directory_query_requires_trailing_slash():
    with pytest.raises(ValueError, match=r".+") as exc:
        DirectoryQuery("/reports")

    assert str(exc.value) == ("Directory URIs must end with a forward slash.")


def test_directory_query_with_defaults():
    query = DirectoryQuery("/reports/")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<directory-query>"
        "<uri>/reports/</uri>"
        "</directory-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
