from mlclient.search.structured import PathIndex


def run():
    return PathIndex("/x:report", {"xml": "https://example.com/other"})
