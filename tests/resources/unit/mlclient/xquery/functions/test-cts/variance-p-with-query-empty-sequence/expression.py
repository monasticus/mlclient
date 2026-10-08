from mlclient.xquery import cts


def run():
    return cts.variance_p(cts.element_reference("price"), query=None).compile()
