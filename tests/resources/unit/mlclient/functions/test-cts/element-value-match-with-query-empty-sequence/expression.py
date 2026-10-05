from mlclient.functions.xqy import cts


def run():
    return cts.element_value_match("item", "prod*", query=None).compile()
