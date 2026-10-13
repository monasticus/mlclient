from mlclient.xquery import cts


def run():
    return cts.document_query(None).compile()
