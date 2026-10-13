from mlclient.xquery import cts


def run():
    return cts.element_value_co_occurrences("item", "item", quality_weight=set())
