from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_value_co_occurrences(
        "item", "id", "item", "id", options=set(),
    )
