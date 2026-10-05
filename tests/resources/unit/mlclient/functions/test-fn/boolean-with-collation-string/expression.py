from mlclient.functions.xqy import cts, fn


def run():
    return fn.boolean(
        cts.search().pos(1), collation="http://marklogic.com/collation/codepoint",
    ).compile()
