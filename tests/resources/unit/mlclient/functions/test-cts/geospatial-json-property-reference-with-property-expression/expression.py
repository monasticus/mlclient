from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_json_property_reference(
        fn.string(cts.search().pos(1)),
    ).compile()
