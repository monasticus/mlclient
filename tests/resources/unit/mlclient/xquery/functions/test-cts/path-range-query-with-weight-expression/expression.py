from mlclient.xquery import cts, fn


def run():
    return cts.path_range_query(
        "/p:item", "=", "value", weight=fn.count(cts.search().pos(1)),
    ).compile()
