from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_value_ranges("item", "id", options="checked").compile()
