from mlclient.functions.xqy import cts


def run():
    return cts.element_value_query("item", options="checked").compile()
