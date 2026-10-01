from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_region_path_reference(
        "/p:item", units=fn.string(cts.search().index(1)),
    ).compile()
