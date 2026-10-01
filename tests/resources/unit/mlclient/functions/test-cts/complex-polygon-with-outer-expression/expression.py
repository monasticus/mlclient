from mlclient.functions.xqy import cts


def run():
    return cts.complex_polygon(
        cts.box(10, 10, 20, 20), cts.box(10, 10, 20, 20),
    ).compile()
