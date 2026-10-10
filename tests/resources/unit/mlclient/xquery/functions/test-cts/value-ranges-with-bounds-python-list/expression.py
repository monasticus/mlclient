from mlclient.xquery import cts


def run():
    return cts.value_ranges(
        cts.element_reference("price"), bounds=["bounds", 123, 2.5, True],
    ).compile()
