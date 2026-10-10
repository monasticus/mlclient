from mlclient.xquery import cts


def run():
    return cts.document_format_query("xml").compile()
