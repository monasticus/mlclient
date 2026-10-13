from mlclient.xquery import cts


def run():
    return cts.covariance_p(set(), cts.element_reference("price"))
