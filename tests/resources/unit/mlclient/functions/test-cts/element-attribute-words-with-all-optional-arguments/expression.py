from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_words(
        "item",
        "id",
        start="a",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
