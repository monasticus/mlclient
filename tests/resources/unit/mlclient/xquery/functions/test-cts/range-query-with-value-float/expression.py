from mlclient.xquery import cts


def run():
    return cts.range_query(cts.element_reference("price"), "=", 2.5).compile()
