from mlclient.functions.xqy import cts


def run():
    return cts.correlation(set(), cts.element_reference("price"))
