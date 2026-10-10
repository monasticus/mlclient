from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = ElementTree(element)
    expression = fn.key(fn.string("auxiliary"), fn.string("auxiliary"), top=node)
    return expression.compile()
