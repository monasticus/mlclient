from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_region_path_reference(
        fn.string(cts.search().pos(1)),
    ).compile()
