from mlclient.functions.xqy import cts


def run():
    return cts.stddev(cts.element_reference("price"), query=None).compile()
