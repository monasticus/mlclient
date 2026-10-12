from mlclient.search.structured import PathIndex


def run():
    return PathIndex("/x:report", {"search": "https://example.com/other"})
