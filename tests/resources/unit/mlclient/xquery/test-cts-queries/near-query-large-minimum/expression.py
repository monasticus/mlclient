from mlclient.xquery import cts


def run():
    return cts.near_query([], options="minimum-distance=4294967296")
