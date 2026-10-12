from mlclient.search.structured import PathIndex


def run():
    return PathIndex("/x:report", {"": "https://example.com/other"})
