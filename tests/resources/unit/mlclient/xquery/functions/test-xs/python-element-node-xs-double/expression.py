from xml.etree.ElementTree import fromstring
from mlclient.xquery import xs


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = element
    expression = xs.double(node)
    return expression.compile()
