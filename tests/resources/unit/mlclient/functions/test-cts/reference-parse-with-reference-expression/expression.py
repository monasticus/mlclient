from mlclient.functions.xqy import cts


def run():
    return cts.reference_parse(cts.element_reference("price")).compile()
