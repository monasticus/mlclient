from mlclient.xquery import cts


def run():
    return cts.correlation(
        cts.element_reference("price"), cts.element_reference("price"), forest_ids=None,
    ).compile()
