from mlclient.xquery import cts


def run():
    return cts.document_root_query("root").compile()
