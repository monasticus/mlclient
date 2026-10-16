from mlclient.search.options import Range, opt
from mlclient.search.structured import Element


def run():
    return opt.options(
        opt.values(
            "price",
            Range(Element("price"), "xs:decimal"),
            options="frequency-order",
        ),
    )
