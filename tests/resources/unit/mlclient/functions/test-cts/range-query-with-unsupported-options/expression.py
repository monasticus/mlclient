from mlclient.functions.xqy import cts


def run():
    return cts.range_query(cts.element_reference("price"), "=", "value", options=set())
