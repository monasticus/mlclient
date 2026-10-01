from mlclient.functions.xqy import cts


def run():
    return cts.linear_model(
        cts.search().index(1), options="checked", query="needle", forest_ids=123,
    ).compile()
