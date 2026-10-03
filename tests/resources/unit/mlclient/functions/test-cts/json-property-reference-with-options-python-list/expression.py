from mlclient.functions.xqy import cts


def run():
    return cts.json_property_reference("price", options=["checked"]).compile()
