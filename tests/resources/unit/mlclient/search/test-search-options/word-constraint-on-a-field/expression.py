from mlclient.search.options import SearchOptions, WordConstraint
from mlclient.search.structured import Field


def run():
    return SearchOptions(WordConstraint("summary", Field("summary")))
