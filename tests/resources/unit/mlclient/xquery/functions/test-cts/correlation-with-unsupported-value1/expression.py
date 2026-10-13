from mlclient.xquery import cts


def run():
    return cts.correlation(set(), cts.element_reference("price"))
