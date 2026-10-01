from mlclient.functions.xqy import cts, fn


def run():
    return cts.path_range_query(
        "/p:item", fn.string(cts.search().index(1)), "value",
    ).compile()
