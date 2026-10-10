from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import cts


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = cts.relevance_info(node=node)
    return expression.compile()
