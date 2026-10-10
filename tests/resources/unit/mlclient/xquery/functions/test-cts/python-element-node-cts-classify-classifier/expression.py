from xml.etree.ElementTree import fromstring
from mlclient.xquery import cts, fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = element
    expression = cts.classify(fn.string("auxiliary"), node)
    return expression.compile()
