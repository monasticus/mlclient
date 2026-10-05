from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_range_query(
        "price", fn.string(cts.search().pos(1)), "value",
    ).compile()
