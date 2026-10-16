"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import opt
from mlclient.search.structured import Element


def run():
    return opt.options(opt.container_constraint("place", Element("location")))
