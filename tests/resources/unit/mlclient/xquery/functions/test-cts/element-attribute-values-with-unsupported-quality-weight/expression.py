from mlclient.xquery import cts


def run():
    return cts.element_attribute_values("item", "id", quality_weight=set())
