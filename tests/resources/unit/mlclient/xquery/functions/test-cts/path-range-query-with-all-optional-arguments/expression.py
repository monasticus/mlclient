from mlclient.xquery import cts


def run():
    return cts.path_range_query(
        "/p:item", "=", "value", options="checked", weight=2.5,
    ).compile()
