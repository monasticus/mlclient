xquery version "1.0-ml";
declare variable $v0 as xs:string external;
cts:part-of-speech(cts:tokenize($v0))
