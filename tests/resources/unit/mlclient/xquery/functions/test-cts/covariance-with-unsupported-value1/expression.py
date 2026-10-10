from mlclient.xquery import cts


def run():
    return cts.covariance(set(), cts.element_reference("price"))
