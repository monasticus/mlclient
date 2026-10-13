xquery version "1.0-ml";
import module namespace temporal = "http://marklogic.com/xdmp/temporal"
    at "/MarkLogic/temporal.xqy";

(
    temporal:axis-create(
        "system",
        xs:QName("systemStart") => cts:element-reference(),
        xs:QName("systemEnd") => cts:element-reference()
    ),
    temporal:axis-create(
        "valid",
        xs:QName("validStart") => cts:element-reference(),
        xs:QName("validEnd") => cts:element-reference()
    )
)
