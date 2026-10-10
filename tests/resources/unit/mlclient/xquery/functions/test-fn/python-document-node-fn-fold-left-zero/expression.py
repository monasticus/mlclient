from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = fn.fold_left(fn.string("auxiliary"), node, fn.string("auxiliary"))
    return expression.compile()
