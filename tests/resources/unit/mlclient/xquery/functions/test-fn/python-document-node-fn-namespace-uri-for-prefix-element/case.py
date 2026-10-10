from xml.etree.ElementTree import ElementTree, fromstring, tostring
from mlclient.xquery import fn, xdmp


def run():
    element = fromstring('<report xmlns="urn:reports">blue</report>')
    node = ElementTree(element)
    expected = xdmp.unquote(
        tostring(element, encoding="unicode").replace("ns0", "node0"),
    )
    expression = fn.namespace_uri_for_prefix(fn.string("auxiliary"), node)
    original = expression.compile()
    assert (
        original
        == fn.namespace_uri_for_prefix(fn.string("auxiliary"), expected).compile()
    )
    assert "blue" not in original[0]
    assert any("blue" in str(value) for value in original[1].values())
    element.text = "changed"
    assert expression.compile() == original
