from mlclient.search.structured import PathIndex


def run():
    return PathIndex("/r:report/r:price", {"r": "https://example.com/example/reports"})
