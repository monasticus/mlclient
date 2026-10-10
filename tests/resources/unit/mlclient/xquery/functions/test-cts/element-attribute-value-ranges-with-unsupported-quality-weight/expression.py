from mlclient.xquery import cts


def run():
    return cts.element_attribute_value_ranges("item", "id", quality_weight=set())
