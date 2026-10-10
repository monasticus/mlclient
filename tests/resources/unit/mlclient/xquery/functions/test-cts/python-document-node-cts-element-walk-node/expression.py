from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import cts, fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = cts.element_walk(node, fn.string("auxiliary"), fn.string("auxiliary"))
    return expression.compile()
