from mlclient.xquery import cts


def run():
    return cts.element_value_ranges("item", query=None).compile()
