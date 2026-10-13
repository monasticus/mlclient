"Public compilation and native serialization of SimilarQuery."

from mlclient.xquery import FunctionCall, cts


def run():
    options = (
        '<options xmlns="cts:distinctive-terms"><min-val>1</min-'
        "val><min-weight>2</min-weight><complete>true</complete>"
        "</options>"
    )
    return cts.similar_query(
        None,
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
