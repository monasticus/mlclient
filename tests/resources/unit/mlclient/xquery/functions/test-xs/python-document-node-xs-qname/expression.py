from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import xs


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = xs.qname(node)
    return expression.compile()
