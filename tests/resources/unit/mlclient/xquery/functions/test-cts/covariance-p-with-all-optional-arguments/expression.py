from mlclient.xquery import cts


def run():
    return cts.covariance_p(
        cts.element_reference("price"),
        cts.element_reference("price"),
        options="checked",
        query="needle",
        forest_ids=123,
    ).compile()
