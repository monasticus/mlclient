from mlclient.search.options import opt
from mlclient.search.structured import Attribute, Element


def run():
    return opt.options(
        opt.word_constraint("code", Element("item"), attribute=Attribute("code")),
    )
