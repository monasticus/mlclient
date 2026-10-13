from mlclient.xquery import cts


def run():
    return cts.range_query(cts.element_reference("price"), set(), "value")
