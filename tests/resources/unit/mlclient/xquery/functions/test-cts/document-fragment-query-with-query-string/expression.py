from mlclient.xquery import cts


def run():
    return cts.document_fragment_query("needle").compile()
