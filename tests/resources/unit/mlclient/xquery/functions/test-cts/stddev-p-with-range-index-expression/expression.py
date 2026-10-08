from mlclient.xquery import cts


def run():
    return cts.stddev_p(cts.element_reference("price")).compile()
