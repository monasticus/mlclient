from mlclient.xquery import cts


def run():
    return cts.element_attribute_range_query(
        "item", "id", "=", ["value", 123, 2.5, True],
    ).compile()
