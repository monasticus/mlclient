from mlclient.xquery import cts


def run():
    return cts.element_attribute_range_query(
        "item",
        "amount",
        "!=",
        3,
        options="cached",
        weight=3,
    )
