from mlclient.xquery import cts, fn


def run():
    return cts.json_property_range_query(
        "price", "=", "value", weight=fn.count(cts.search().pos(1)),
    ).compile()
