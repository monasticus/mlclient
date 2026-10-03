from mlclient.functions.xqy import cts


def run():
    return cts.element_value_ranges("item", quality_weight=2.5).compile()
