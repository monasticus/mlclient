from mlclient.xquery import cts


def run():
    return cts.values(cts.element_reference("price"), start=123).compile()
