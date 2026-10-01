from mlclient.functions.xqy import cts, fn


def run():
    return cts.covariance_p(
        cts.element_reference("price"),
        cts.element_reference("price"),
        forest_ids=fn.count(cts.search().index(1)),
    ).compile()
