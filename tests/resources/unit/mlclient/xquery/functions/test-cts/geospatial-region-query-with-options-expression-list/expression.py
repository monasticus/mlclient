from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_region_query(
        cts.geospatial_element_reference("region"),
        "operation",
        cts.box(10, 10, 20, 20),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
