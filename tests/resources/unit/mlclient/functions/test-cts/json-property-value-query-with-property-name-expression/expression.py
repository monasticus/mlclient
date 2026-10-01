from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_value_query(
        fn.string(cts.search().index(1)), "value",
    ).compile()
