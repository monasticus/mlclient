from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_json_property_child_reference(
        fn.string(cts.search().index(1)), "child",
    ).compile()
