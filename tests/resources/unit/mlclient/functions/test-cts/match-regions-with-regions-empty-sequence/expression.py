from mlclient.functions.xqy import cts


def run():
    return cts.match_regions(
        cts.element_reference("price"), "operation", None,
    ).compile()
