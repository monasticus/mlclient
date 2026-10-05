from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_value_query(
        "item", "id", ["MarkLogic search"],
    ).compile()
