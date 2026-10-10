from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = fn.root(node)
    return expression.compile()
