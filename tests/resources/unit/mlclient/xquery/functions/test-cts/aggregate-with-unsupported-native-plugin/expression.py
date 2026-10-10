from mlclient.xquery import cts


def run():
    return cts.aggregate(set(), "total", cts.element_reference("price"))
