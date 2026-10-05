from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_region_query(
        cts.geospatial_element_reference("region"),
        fn.string(cts.search().pos(1)),
        cts.box(10, 10, 20, 20),
    ).compile()
