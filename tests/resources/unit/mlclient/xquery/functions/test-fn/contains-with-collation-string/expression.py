from mlclient.xquery import fn


def run():
    return fn.contains(
        "parameter1", "parameter2", collation="http://marklogic.com/collation/codepoint",
    ).compile()
