from mlclient.xquery import cts


def run():
    return cts.variance(cts.element_reference("price"), query="needle").compile()
