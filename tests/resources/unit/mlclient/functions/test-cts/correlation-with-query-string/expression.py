from mlclient.functions.xqy import cts


def run():
    return cts.correlation(
        cts.element_reference("price"), cts.element_reference("price"), query="needle",
    ).compile()
