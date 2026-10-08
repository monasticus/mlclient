from mlclient.xquery import cts, fn


def run():
    return cts.path_range_query(
        "/p:item", fn.string(cts.search().pos(1)), "value",
    ).compile()
