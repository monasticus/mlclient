from mlclient.xquery import cts


def run():
    return cts.element_values(["item"]).compile()
