from mlclient.xquery import cts


def run():
    return cts.geospatial_region_query(
        cts.geospatial_element_reference("region"), set(), cts.box(10, 10, 20, 20),
    )
