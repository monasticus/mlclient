from mlclient.xquery import cts


def run():
    return cts.index_order(cts.element_reference("price"), options=set())
