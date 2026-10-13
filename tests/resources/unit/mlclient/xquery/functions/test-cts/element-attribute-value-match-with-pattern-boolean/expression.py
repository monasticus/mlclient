from mlclient.xquery import cts


def run():
    return cts.element_attribute_value_match("item", "id", True).compile()
