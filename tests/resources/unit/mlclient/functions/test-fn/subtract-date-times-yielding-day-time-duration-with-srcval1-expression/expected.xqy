xquery version "1.0-ml";
declare variable $v0 as xs:dateTime external;
fn:subtract-dateTimes-yielding-dayTimeDuration(fn:current-dateTime(), $v0)
