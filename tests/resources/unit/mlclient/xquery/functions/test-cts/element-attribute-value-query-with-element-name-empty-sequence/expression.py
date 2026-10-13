from mlclient.xquery import cts


def run():
    return cts.element_attribute_value_query(None, "id", "MarkLogic search").compile()
