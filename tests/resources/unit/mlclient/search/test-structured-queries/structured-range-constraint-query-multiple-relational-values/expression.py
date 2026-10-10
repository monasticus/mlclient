from mlclient.search.structured import RangeConstraintQuery


def run():
    return RangeConstraintQuery("price", [3, 4], operator="GT").serialize("xml")
