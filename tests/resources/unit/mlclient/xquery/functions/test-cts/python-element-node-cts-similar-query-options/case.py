from xml.etree.ElementTree import fromstring, tostring
from mlclient.xquery import cts, fn, xdmp


def run():
    element = fromstring('<report xmlns="urn:reports">blue</report>')
    node = element
    expected = xdmp.unquote(
        tostring(element, encoding="unicode").replace("ns0", "node0"),
    )
    expected = expected.xpath("*")
    expression = cts.similar_query(fn.string("auxiliary"), options=node)
    original = expression.compile()
    assert (
        original
        == cts.similar_query(fn.string("auxiliary"), options=expected).compile()
    )
    assert "blue" not in original[0]
    assert any("blue" in str(value) for value in original[1].values())
    element.text = "changed"
    assert expression.compile() == original
