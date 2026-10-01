from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_region_query(
        cts.geospatial_element_reference("region"),
        "operation",
        cts.box(10, 10, 20, 20),
        weight=fn.count(cts.search().index(1)),
    ).compile()
