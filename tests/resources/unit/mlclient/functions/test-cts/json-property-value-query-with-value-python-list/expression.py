from mlclient.functions.xqy import cts


def run():
    return cts.json_property_value_query("price", ["value", 123, 2.5, True]).compile()
