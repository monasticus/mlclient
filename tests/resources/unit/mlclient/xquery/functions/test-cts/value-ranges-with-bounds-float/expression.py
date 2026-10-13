from mlclient.xquery import cts


def run():
    return cts.value_ranges(cts.element_reference("price"), bounds=2.5).compile()
