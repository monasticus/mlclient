from mlclient.functions.xqy import fn


def run():
    return fn.index_of(
        "seq-param",
        "srch-param",
        collation_literal="http://marklogic.com/collation/codepoint",
    ).compile()
