from mlclient.functions.xqy import cts


def run():
    return cts.match_regions(
        cts.element_reference("price"), set(), cts.box(10, 10, 20, 20),
    )
