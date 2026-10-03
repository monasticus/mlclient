from mlclient.functions.xqy import cts


def run():
    return cts.json_property_value_query("price", "value", weight=None).compile()
