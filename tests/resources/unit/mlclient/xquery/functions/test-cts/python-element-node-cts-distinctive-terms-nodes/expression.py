from xml.etree.ElementTree import fromstring
from mlclient.xquery import cts


def run():
    element = fromstring('<report xmlns="https://example.com/reports">blue</report>')
    node = element
    expression = cts.distinctive_terms(node)
    return expression.compile()
