from mlclient.xquery import cts


def run():
    return cts.element_values("item", start=2.5).compile()
