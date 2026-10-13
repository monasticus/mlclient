from mlclient.xquery import cts


def run():
    return cts.stddev(cts.element_reference("price"), query="needle").compile()
