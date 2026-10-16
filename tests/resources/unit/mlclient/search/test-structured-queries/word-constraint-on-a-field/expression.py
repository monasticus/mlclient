from mlclient.search.options import opt
from mlclient.search.structured import Field


def run():
    return opt.options(opt.word_constraint("summary", Field("summary")))
