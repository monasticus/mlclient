from mlclient.search.options import WordConstraint
from mlclient.search.structured import sq


def run():
    return WordConstraint("title", sq.element("title"))
