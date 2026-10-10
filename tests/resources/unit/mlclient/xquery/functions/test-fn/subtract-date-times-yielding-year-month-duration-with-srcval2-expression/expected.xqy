xquery version "1.0-ml";
declare variable $v0 as xs:dateTime external;
fn:subtract-dateTimes-yielding-yearMonthDuration($v0, fn:current-dateTime())
