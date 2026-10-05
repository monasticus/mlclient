from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_value_co_occurrences(
        "item", None, "item", "id",
    ).compile()
