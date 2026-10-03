from mlclient.functions.xqy import cts


def run():
    return cts.value_ranges(cts.element_reference("price")).compile()
