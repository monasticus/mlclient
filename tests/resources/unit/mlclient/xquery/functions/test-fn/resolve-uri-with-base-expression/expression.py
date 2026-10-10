from mlclient.xquery import cts, fn


def run():
    return fn.resolve_uri(
        "items/1.xml", base=fn.string(cts.search().pos(1)),
    ).compile()
