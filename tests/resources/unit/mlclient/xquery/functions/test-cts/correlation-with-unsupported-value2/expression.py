from mlclient.xquery import cts


def run():
    return cts.correlation(cts.element_reference("price"), set())
