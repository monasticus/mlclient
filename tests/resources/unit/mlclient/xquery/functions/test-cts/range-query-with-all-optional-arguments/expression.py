from mlclient.xquery import cts


def run():
    return cts.range_query(
        cts.element_reference("price"), "=", "value", options="checked", weight=2.5,
    ).compile()
