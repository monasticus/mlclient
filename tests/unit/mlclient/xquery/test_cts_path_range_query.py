"""Native ``cts:path-range-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import PathRangeQuery, cts


def test_path_range_query():
    query = cts.path_range_query("/item/price", ">", 1)
    assert isinstance(query, PathRangeQuery)
    assert query.serialize() == {
        "pathRangeQuery": {
            "pathExpression": ["/item/price"],
            "operator": ">",
            "value": [{"type": "decimal", "val": "1"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:path-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi="ht'
        'tp://www.w3.org/2001/XMLSchema-instance" operator="&gt;">'
        "<cts:path-expression>/item/price</cts:path-expression>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:inte'
        'ger">1'
        "</cts:value></cts:path-range-query>"
    )
