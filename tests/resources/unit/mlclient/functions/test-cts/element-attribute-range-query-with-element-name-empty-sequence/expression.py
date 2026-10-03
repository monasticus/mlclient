from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_range_query(None, "id", "=", "value").compile()
