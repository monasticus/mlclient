from mlclient.xquery import cts


def run():
    return cts.json_property_range_query(None, "=", "value").compile()
