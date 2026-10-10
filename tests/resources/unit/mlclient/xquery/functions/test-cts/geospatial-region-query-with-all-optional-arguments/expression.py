from mlclient.xquery import cts


def run():
    return cts.geospatial_region_query(
        cts.geospatial_element_reference("region"),
        "operation",
        cts.box(10, 10, 20, 20),
        options="checked",
        weight=2.5,
    ).compile()
