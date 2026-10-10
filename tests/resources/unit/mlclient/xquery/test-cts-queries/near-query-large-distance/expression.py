from mlclient.xquery import cts


def run():
    return cts.near_query([], distance=1000000000000)
