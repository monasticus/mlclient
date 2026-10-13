from mlclient.xquery import cts


def run():
    return cts.directory_query(None).compile()
