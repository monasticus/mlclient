from xml.etree.ElementTree import fromstring
from mlclient.xquery import xdmp


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = element
    expression = xdmp.unquote(node)
    return expression.compile()
