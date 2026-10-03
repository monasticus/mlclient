from mlclient.functions.xqy import cts


def run():
    return cts.element_values("item", start=123).compile()
