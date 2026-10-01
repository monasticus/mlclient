from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_range_query(
        [fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
        "=",
        "value",
    ).compile()
