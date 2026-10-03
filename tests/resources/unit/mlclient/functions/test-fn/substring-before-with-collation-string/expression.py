from mlclient.functions.xqy import fn


def run():
    return fn.substring_before(
        "MarkLogic", "needle", collation="http://marklogic.com/collation/codepoint",
    ).compile()
