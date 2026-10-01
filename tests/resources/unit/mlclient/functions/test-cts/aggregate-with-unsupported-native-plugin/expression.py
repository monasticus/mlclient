from mlclient.functions.xqy import cts


def run():
    return cts.aggregate(set(), "total", cts.element_reference("price"))
