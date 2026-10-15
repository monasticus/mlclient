xquery version "1.0-ml";

if (xdmp:get-request-path() = "/orders.xqy") then "/orders.xqy" else "/health.xqy"
