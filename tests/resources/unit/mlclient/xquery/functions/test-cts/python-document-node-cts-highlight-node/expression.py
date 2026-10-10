from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import cts, fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = cts.highlight(node, cts.true_query(), fn.string("auxiliary"))
    return expression.compile()
