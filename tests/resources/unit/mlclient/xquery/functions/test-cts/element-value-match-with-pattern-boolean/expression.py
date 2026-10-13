from mlclient.xquery import cts


def run():
    return cts.element_value_match("item", True).compile()
