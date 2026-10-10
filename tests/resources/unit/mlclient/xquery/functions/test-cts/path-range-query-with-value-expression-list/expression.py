from mlclient.xquery import cts, fn


def run():
    return cts.path_range_query(
        "/p:item",
        "=",
        [fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
