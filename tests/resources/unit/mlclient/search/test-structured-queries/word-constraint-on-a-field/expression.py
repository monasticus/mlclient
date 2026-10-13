from mlclient.search.options import SearchOptions
from mlclient.search.structured import Field


def run():
    return SearchOptions().word_constraint("summary", Field("summary"))
