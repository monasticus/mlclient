Output "docs/assets/gifs/eval.gif"
Require ml

Set Shell "bash"
Set Width 940
Set Height 500
Set Theme "Gruvbox Light"
Set FontFamily "JetBrains Mono"
Set FontSize 16
Set Padding 30
Set BorderRadius 0
Set Margin 0
Set LetterSpacing 1
Set LineHeight 1.2
Set CursorBlink true
Set TypingSpeed 50ms

Hide
Set TypingSpeed 1ms
Type `unset NO_COLOR HISTIGNORE HISTCONTROL; HISTSIZE=100; HISTFILE=/dev/null; set -o history; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; mkdir .mlclient; printf 'host: localhost\nusername: admin\npassword: admin\napp-servers:\n  - id: app-services\n    port: 18000\n    rest: true\n' > .mlclient/mlclient-local.yaml; cp .mlclient/mlclient-local.yaml .mlclient/mlclient-qa.yaml; sed s/18000/8000/ .mlclient/mlclient-local.yaml > .mlclient/mlclient-dev.yaml`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `test "$(ml eval -x 'empty(cts:uri-match("/order/*"))' | tail -n 1)" = true || exit 1`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `test "$(ml eval -e dev -x 'fn:doc-available("/mlclient-vhs-multi-env/catalog.xml")' | tail -n 1)" = false || exit 1`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `printf '%s\n' 'for $id in (1001, 1002, 1003) return xdmp:document-delete(concat("/order/", $id, ".xml"))' > cleanup.xqy; printf '%s\n' 'xdmp:document-delete("/mlclient-vhs-multi-env/catalog.xml")' > cleanup-dev.xqy; trap 'ml eval cleanup.xqy >/dev/null; ml eval -e dev cleanup-dev.xqy >/dev/null; rm -rf "$demo_dir"' EXIT`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `ml eval -x 'for $id in (1001, 1002, 1003) return xdmp:document-insert(concat("/order/", $id, ".xml"), <order id="{$id}"><customer>Ada</customer><status>{if ($id = 1003) then "pending" else "paid"}</status><total currency="EUR">29.90</total></order>, xdmp:default-permissions(), ("orders", if ($id = 1003) then "pending" else "paid"))'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `ml eval -e dev -x 'xdmp:document-insert("/mlclient-vhs-multi-env/catalog.xml", <catalog><book>MarkLogic</book></catalog>, xdmp:default-permissions(), ("books", "catalog"))'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `printf '%s\n' 'declare variable $status external; <report><status>{$status}</status><orders>{count(collection()/order[status = $status])}</orders></report>' > report.xqy; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type `ml eval -x 'cts:uri-match("/order/*")'`
Enter
Wait
Wait+Screen /1003.xml/
Sleep 2s
Up
Ctrl+E
Left
Type "[1] => fn:doc()"
Enter
Wait
Wait+Screen /<customer>Ada/
Sleep 3s
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type "ml eval -j '"
Type '`Server time: ${fn.currentTime()}`'
Type "'"
Enter
Wait
Wait+Screen /Server time:/
Sleep 2s
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type "ml eval report.xqy -e qa --var status=paid"
Enter
Wait
Wait+Screen /<orders>2/
Sleep 3s
Up
Ctrl+W
Type "status=pending"
Enter
Wait
Wait+Screen /<orders>1/
Sleep 3s

Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type "ml eval -e local -e dev -x 'cts:estimate(cts:true-query())'"
Enter
Wait
Wait+Screen /local.*dev/
Sleep 4s
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type "ml eval -e local -e dev -x 'cts:collections()'"
Enter
Wait
Wait+Screen /orders/
Wait+Screen /catalog/
Sleep 5s
