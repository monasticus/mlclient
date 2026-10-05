from mlclient.functions.xqy import cts


def run():
    return cts.field_range_query(
        "description", "=", "value", options="checked", weight=2.5,
    ).compile()
