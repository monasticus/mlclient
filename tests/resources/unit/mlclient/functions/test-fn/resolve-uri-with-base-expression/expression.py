from mlclient.functions.xqy import cts, fn


def run():
    return fn.resolve_uri(
        "items/1.xml", base=fn.string(cts.search().index(1)),
    ).compile()
