from mlclient.search.structured import RangeConstraintQuery


def run():
    return RangeConstraintQuery("price", []).serialize("xml")
