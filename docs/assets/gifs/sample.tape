Output "docs/assets/gifs/sample.gif"
Require ml
Require docker
# Requires the disposable vhs-docs-demo REST instance on MarkLogic 12 port 8008.

Set Shell "bash"
Set Width 800
Set Height 480
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
Type `unset NO_COLOR; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; mkdir .mlclient; dev_host=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mlclient_cts_query_12); printf 'host: ml-dev.%s.nip.io\nusername: admin\npassword: admin\napp-servers:\n  - id: app-services\n    port: 8008\n    rest: true\n' "$dev_host" > .mlclient/mlclient-local.yaml`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `trap 'for uri in /sample-order.xml /customer-1.json /customer-2.json /customer-3.json; do ml http delete /v1/documents uri="$uri" >/dev/null; done; rm -rf "$demo_dir"' EXIT`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `ml http put /v1/documents uri=/sample-order.xml Content-Type:application/xml -b '<order id="1001"><item sku="A1">Tea</item><item sku="B2">Coffee</item><item sku="C3">Cocoa</item><item sku="D4">Honey</item><item sku="E5">Milk</item></order>'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `ml http put /v1/documents uri=/customer-1.json Content-Type:application/json -b '{"name":"Ada","address":{"city":"London","zip":"N1"}}'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `ml http put /v1/documents uri=/customer-2.json Content-Type:application/json -b '{"name":"Tom","address":{"city":"Warsaw","zip":"00-001"}}'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `ml http put /v1/documents uri=/customer-3.json Content-Type:application/json -b '{"name":"Mia","address":{"city":"Berlin","zip":"10115"}}'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml sample order`
Enter
Wait
Sleep 3s
Type `ml sample '/order/item' -l 3`
Enter
Wait
Sleep 3s
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml sample -j address`
Enter
Wait
Sleep 3s
Type `ml sample -j / -l 3 --no-pretty`
Enter
Wait
Sleep 4s
