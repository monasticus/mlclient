from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import cts


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = cts.reference_parse(node)
    return expression.compile()
