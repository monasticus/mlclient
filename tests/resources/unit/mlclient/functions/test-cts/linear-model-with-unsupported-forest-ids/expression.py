from mlclient.functions.xqy import cts


def run():
    return cts.linear_model(cts.search().pos(1), forest_ids=set())
