"""Runtime CTS queries compile but cannot be described without evaluation."""

from mlclient.xquery import FunctionCall, cts


def run():
    return cts.query(FunctionCall("fn:doc", ("/query.xml",))).to_xml()
