from mlclient.functions.xqy import cts


def run():
    return cts.element_value_ranges(
        "item",
        bounds="bounds",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
