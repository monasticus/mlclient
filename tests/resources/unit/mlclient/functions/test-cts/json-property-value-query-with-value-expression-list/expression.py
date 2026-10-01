from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_value_query(
        "price", [fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
