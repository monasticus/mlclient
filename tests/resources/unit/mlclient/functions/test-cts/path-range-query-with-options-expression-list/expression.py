from mlclient.functions.xqy import cts, fn


def run():
    return cts.path_range_query(
        "/p:item",
        "=",
        "value",
        options=[fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
