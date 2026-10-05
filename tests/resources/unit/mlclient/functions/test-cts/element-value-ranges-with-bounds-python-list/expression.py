from mlclient.functions.xqy import cts


def run():
    return cts.element_value_ranges("item", bounds=["bounds", 123, 2.5, True]).compile()
