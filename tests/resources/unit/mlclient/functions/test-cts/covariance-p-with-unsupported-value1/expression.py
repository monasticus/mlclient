from mlclient.functions.xqy import cts


def run():
    return cts.covariance_p(set(), cts.element_reference("price"))
