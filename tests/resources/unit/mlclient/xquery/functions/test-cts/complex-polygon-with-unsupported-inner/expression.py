from mlclient.xquery import cts


def run():
    return cts.complex_polygon(cts.box(10, 10, 20, 20), set())
