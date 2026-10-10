"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range


def run():
    return Range("price").to_json()
