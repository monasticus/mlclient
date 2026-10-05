from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_values(None, "id").compile()
