from mlclient.xquery import cts


def run():
    return cts.element_attribute_reference("item", "id", options=["checked"]).compile()
