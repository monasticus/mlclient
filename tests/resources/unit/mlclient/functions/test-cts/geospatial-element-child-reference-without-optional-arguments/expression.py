from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_element_child_reference("item", "child").compile()
