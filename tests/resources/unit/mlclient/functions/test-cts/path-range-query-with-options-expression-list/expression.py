from mlclient.functions.xqy import cts, fn


def run():
    return cts.path_range_query(
        "/p:item",
        "=",
        "value",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
