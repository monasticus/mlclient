"""Native word-query serialization through the public CTS builder."""

from mlclient.xquery import FunctionCall, cts


def run():
    return cts.word_query("blue", weight=FunctionCall("xs:double", (2, 3))).serialize()
