from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import xdmp


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = xdmp.unquote(node)
    return expression.compile()
