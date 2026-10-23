from mlclient.search import sq
from mlclient.search.options import WordConstraint


def run():
    return WordConstraint("title", sq.element("title"))
