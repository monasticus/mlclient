from mlclient.xquery import cts


def run():
    return cts.match_regions(cts.element_reference("price"), "operation", set())
