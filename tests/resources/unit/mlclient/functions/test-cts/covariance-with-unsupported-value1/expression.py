from mlclient.functions.xqy import cts


def run():
    return cts.covariance(set(), cts.element_reference("price"))
