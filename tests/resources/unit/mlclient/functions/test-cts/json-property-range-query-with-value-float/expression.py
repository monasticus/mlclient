from mlclient.functions.xqy import cts


def run():
    return cts.json_property_range_query("price", "=", 2.5).compile()
