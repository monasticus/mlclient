from mlclient.functions.xqy import cts


def run():
    return cts.value_tuples(cts.element_reference("price")).compile()
