Output "docs/assets/gifs/http.gif"
Require ml
Require docker
# Requires the disposable vhs-docs-demo REST instance on MarkLogic 12 port 8008.

Set Shell "bash"
Set Width 940
Set Height 560
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
Type `trap 'ml http delete /v1/documents uri=/doc1.json >/dev/null; ml http delete /v1/documents uri=/doc2.json >/dev/null; ml http delete /v1/documents uri=/doc3.json >/dev/null; rm -rf "$demo_dir"' EXIT`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `ml http put /v1/documents uri=/doc1.json Content-Type:application/json -b '{"hello":"MarkLogic"}'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `printf '%s\n' '{"order":1001,"status":"paid"}' > order.json; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml http get /v1/documents uri=/doc1.json`
Enter
Wait
Sleep 3s
Type `ml http put /v1/documents uri=/doc2.json \`
Enter
Type `  -b '{"hello": "world"}' \`
Enter
Type "  Content-Type:application/json"
Enter
Wait
Sleep 2s
Type `ml http get /v1/documents uri=/doc2.json --pretty`
Enter
Wait
Sleep 3s
Type `ml http delete /v1/documents uri=/doc2.json --include`
Enter
Wait
Sleep 4s

Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type "cat order.json"
Enter
Wait
Sleep 2s
Type `ml http put /v1/documents uri=/doc3.json -b @order.json \`
Enter
Type "  Content-Type:application/json"
Enter
Wait
Sleep 2s
Type "ml http get /v1/documents uri=/doc3.json --pretty"
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
Type "ml http get /manage/v2/users/nobody/properties -c 8002 format=json"
Enter
Wait
Sleep 3s
Type "ml http get /manage/v2/users/nobody/properties -c manage format=json --pretty"
Enter
Wait
Sleep 4s
