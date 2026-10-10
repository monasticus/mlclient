"Public compilation and native serialization of SimilarQuery."

from mlclient.xquery import FunctionCall, cts


def run():
    options = (
        '<options xmlns="cts:distinctive-terms"><max-terms>20</m'
        "ax-terms><score>logtf</score></options>"
    )
    return cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
