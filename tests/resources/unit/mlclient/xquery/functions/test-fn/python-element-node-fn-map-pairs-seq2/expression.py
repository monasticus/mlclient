from xml.etree.ElementTree import fromstring
from mlclient.xquery import fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = element
    expression = fn.map_pairs(fn.string("auxiliary"), fn.string("auxiliary"), node)
    return expression.compile()
