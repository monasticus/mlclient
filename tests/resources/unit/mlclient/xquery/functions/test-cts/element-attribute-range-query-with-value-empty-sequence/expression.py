from mlclient.xquery import cts


def run():
    return cts.element_attribute_range_query("item", "id", "=", None).compile()
