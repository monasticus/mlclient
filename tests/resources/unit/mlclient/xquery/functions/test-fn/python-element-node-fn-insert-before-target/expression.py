from xml.etree.ElementTree import fromstring
from mlclient.xquery import fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = element
    expression = fn.insert_before(node, fn.string("auxiliary"), fn.string("auxiliary"))
    return expression.compile()
