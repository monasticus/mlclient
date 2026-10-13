from mlclient.xquery import cts


def run():
    return cts.entity(set(), "normalized-text", "MarkLogic search", "type")
