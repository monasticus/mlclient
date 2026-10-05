from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_region_query(
        cts.geospatial_element_reference("region"), "operation", None,
    ).compile()
