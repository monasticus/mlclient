from mlclient.xquery import cts


def run():
    return cts.element_attribute_value_ranges(None, "id").compile()
