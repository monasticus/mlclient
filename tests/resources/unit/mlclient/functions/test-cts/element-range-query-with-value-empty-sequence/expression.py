from mlclient.functions.xqy import cts


def run():
    return cts.element_range_query("item", "=", None).compile()
