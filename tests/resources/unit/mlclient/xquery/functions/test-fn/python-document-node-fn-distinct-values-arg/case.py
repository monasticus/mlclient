from xml.etree.ElementTree import ElementTree, fromstring, tostring
from mlclient.xquery import fn, xdmp


def run():
    element = fromstring('<report xmlns="urn:reports">blue</report>')
    node = ElementTree(element)
    expected = xdmp.unquote(
        tostring(element, encoding="unicode").replace("ns0", "node0"),
    )
    expression = fn.distinct_values(node)
    original = expression.compile()
    assert original == fn.distinct_values(expected).compile()
    assert "blue" not in original[0]
    assert any("blue" in str(value) for value in original[1].values())
    element.text = "changed"
    assert expression.compile() == original
