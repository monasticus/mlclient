from mlclient.xquery import cts


def run():
    return cts.json_property_value_query("price", "value", options=None).compile()
