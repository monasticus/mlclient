from mlclient.search.structured import PathIndex


def run():
    return PathIndex("/x:report", {"xmlns": "https://example.com/other"})
