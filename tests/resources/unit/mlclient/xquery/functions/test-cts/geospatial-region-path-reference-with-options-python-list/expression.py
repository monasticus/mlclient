from mlclient.xquery import cts


def run():
    return cts.geospatial_region_path_reference(
        "/p:item", options=["checked"],
    ).compile()
