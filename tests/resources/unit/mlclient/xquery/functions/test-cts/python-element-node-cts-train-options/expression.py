from xml.etree.ElementTree import fromstring
from mlclient.xquery import cts, fn


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = element
    expression = cts.train(fn.string("auxiliary"), fn.string("auxiliary"), options=node)
    return expression.compile()
