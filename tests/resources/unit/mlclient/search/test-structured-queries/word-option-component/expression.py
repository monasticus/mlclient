from mlclient.search.options import opt
from mlclient.search.structured import sq


def run():
    return opt.word_constraint("title", sq.element("title"))
