from mlclient.functions.xqy import cts, fn


def run():
    return cts.and_query(
        "queries",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
