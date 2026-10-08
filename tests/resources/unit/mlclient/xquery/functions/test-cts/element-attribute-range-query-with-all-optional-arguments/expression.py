from mlclient.xquery import cts


def run():
    return cts.element_attribute_range_query(
        "item", "id", "=", "value", options="checked", weight=2.5,
    ).compile()
