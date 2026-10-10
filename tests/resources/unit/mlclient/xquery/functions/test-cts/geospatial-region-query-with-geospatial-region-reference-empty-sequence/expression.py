from mlclient.xquery import cts


def run():
    return cts.geospatial_region_query(
        None, "operation", cts.box(10, 10, 20, 20),
    ).compile()
