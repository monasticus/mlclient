from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_value_match("item", "id", 2.5).compile()
