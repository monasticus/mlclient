from mlclient.functions.xqy import cts, fn


def run():
    return fn.escape_uri(
        "products/Mark Logic", fn.exists(cts.search().index(1)),
    ).compile()
