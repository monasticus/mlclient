from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_region_path_reference(
        "/p:item", geohash_precision=fn.count(cts.search().pos(1)),
    ).compile()
