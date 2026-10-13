from mlclient.xquery import cts


def run():
    return cts.avg_aggregate(cts.element_reference("price"), query=set())
