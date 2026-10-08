from mlclient.xquery import cts


def run():
    return cts.document_permission_query("reader", set())
