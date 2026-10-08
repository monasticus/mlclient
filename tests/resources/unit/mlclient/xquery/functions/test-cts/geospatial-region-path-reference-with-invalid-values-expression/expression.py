from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_region_path_reference(
        "/p:item", invalid_values=fn.string(cts.search().pos(1)),
    ).compile()
