from mlclient.functions.xqy import cts


def run():
    return cts.element_value_co_occurrences("item", "item", query="needle").compile()
