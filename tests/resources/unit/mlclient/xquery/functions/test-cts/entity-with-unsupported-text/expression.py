from mlclient.xquery import cts


def run():
    return cts.entity("id", "normalized-text", set(), "type")
