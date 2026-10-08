from mlclient.xquery import cts, fn


def run():
    return cts.json_property_value_query(
        "price", [fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
