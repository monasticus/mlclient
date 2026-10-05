from mlclient.functions.xqy import cts


def run():
    return cts.stddev_p(cts.element_reference("price"), query="needle").compile()
