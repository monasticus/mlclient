from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.Term(o.TermDefault(o.Range(s.JsonProperty("id"), "xs:int"))),
    )
