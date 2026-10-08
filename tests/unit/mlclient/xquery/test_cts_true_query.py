"""Native true query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import TrueQuery, cts


def test_true_query():
    query = cts.true_query()
    assert isinstance(query, TrueQuery)
    assert query.serialize() == {"trueQuery": {}}
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:true-query xmlns:cts="http://marklogic.com/cts" />'
    )
    assert query.compile() == (
        ('xquery version "1.0-ml";\ncts:true-query()'),
        {},
    )
