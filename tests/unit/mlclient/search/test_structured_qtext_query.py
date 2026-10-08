"""Test QtextQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import QtextQuery


def test_serializes_to_json():
    query = QtextQuery("blue AND green")
    expected = {"qtext": ["blue AND green"]}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = QtextQuery("blue AND green")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<qtext>blue AND green"
        "</qtext>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
