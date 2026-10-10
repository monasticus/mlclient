from xml.etree.ElementTree import fromstring
from mlclient.xquery import FunctionCall


def run():
    expression = FunctionCall("fn:node-kind", (fromstring("<report/>"),))
    assert "fn:node-kind(xdmp:unquote($v0) ! *)" in expression.compile()[1].values()
