"""Native false query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import FalseQuery, cts


def test_false_query():
    query = cts.false_query()
    assert isinstance(query, FalseQuery)
    assert query.serialize() == {"falseQuery": {}}
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:false-query xmlns:cts="http://marklogic.com/cts" />'
    )
    assert query.compile() == (
        ('xquery version "1.0-ml";\ncts:false-query()'),
        {},
    )
