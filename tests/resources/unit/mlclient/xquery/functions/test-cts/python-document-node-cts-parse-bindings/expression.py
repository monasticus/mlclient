from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import cts


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = cts.parse(cts.true_query(), bindings=node)
    return expression.compile()
