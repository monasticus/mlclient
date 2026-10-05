from mlclient.functions.xqy import cts


def run():
    return cts.document_fragment_query("needle").compile()
