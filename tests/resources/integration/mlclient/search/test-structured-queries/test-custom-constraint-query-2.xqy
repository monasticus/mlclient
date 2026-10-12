xquery version "1.0-ml";
declare variable $module external;

xdmp:document-insert("/structured-custom.xqy", text {$module})
