from mlclient.functions.xqy import cts


def run():
    return cts.element_values("item", forest_ids=123).compile()
