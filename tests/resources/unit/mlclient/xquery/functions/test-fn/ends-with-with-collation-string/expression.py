from mlclient.xquery import fn


def run():
    return fn.ends_with(
        "parameter1", "parameter2", collation="http://marklogic.com/collation/codepoint",
    ).compile()
