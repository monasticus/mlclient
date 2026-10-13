from mlclient.xquery import cts


def run():
    return cts.sum_aggregate(cts.element_reference("price"), options=set())
