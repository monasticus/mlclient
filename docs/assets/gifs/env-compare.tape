Output "docs/assets/gifs/env-compare.gif"
Require ml

Set Shell "bash"
Set Width 800
Set Height 500
Set Theme "Gruvbox Light"
Set FontFamily "JetBrains Mono"
Set FontSize 16
Set Padding 30
Set BorderRadius 10
Set Margin 0
Set LetterSpacing 1
Set LineHeight 1.2
Set CursorBlink true
Set TypingSpeed 50ms

Hide
Set TypingSpeed 1ms
Type `unset NO_COLOR; demo_dir=$(mktemp -d /tmp/mlclient-compare.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT`
Enter
Wait
Type `mkdir .mlclient; for spec in dev:8010 qa:8020 prod:8030; do name=${spec%:*}; port=${spec#*:}; printf 'host: ml.example.com\nprotocol: https\nusername: reader\npassword: demo-password\napp-name: bookstore-%s\napp-servers:\n  - id: app\n    port: %s\n' "$name" "$port" > ".mlclient/mlclient-$name.yaml"; done`
Enter
Wait
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env compare dev qa"
Enter
Wait
Wait+Screen /bookstore-qa/
Sleep 4s

Hide
Set TypingSpeed 1ms
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env compare"
Enter
Wait
Wait+Screen /bookstore-prod/
Sleep 5s
