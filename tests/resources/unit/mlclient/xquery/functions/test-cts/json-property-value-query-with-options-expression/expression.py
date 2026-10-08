from mlclient.xquery import cts, fn


def run():
    return cts.json_property_value_query(
        "price", "value", options=fn.string(cts.search().pos(1)),
    ).compile()
