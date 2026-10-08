from mlclient.xquery import cts


def run():
    return cts.field_range_query(
        "description", "=", ["value", 123, 2.5, True],
    ).compile()
