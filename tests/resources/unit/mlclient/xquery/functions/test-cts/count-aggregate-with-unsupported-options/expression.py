from mlclient.xquery import cts


def run():
    return cts.count_aggregate(cts.element_reference("price"), options=set())
