from mlclient.xquery import cts


def run():
    return cts.covariance(cts.element_reference("price"), set())
