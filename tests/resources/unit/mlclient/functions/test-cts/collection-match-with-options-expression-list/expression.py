from mlclient.functions.xqy import cts, fn


def run():
    return cts.collection_match(
        "prod*",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
