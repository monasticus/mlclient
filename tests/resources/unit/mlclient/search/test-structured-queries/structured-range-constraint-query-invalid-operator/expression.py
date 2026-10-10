from mlclient.search.structured import RangeConstraintQuery


def run():
    return RangeConstraintQuery("price", 3, operator="INVALID").serialize("xml")
