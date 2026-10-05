from mlclient.functions.xqy import cts


def run():
    return cts.covariance(cts.element_reference("price"), set())
