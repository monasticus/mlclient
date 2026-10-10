from mlclient.xquery import cts


def run():
    return cts.json_property_range_query(
        "price", "=", "value", options="checked", weight=2.5,
    ).compile()
