from mlclient.functions.xqy import cts


def run():
    return cts.max(cts.element_reference("price"), query="needle").compile()
