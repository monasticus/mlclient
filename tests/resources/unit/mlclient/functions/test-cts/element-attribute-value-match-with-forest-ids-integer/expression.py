from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_value_match(
        "item", "id", "prod*", forest_ids=123,
    ).compile()
