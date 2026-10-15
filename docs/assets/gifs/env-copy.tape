Output "docs/assets/gifs/env-copy.gif"
Require vi
Require ml

Set Shell "bash"
Set Width 800
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
Type `unset NO_COLOR; export VISUAL="vi"; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; mkdir .mlclient; printf 'app-name: bookstore\nprotocol: http\nhost: dev.example.com\nusername: reader\npassword: demo-password\nauth: digest\napp-servers:\n  - id: app-services\n    port: 8000\n    rest: true\n' > .mlclient/mlclient-dev.yaml; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env copy dev qa"
Enter
Wait
Wait+Screen /Copied/
Sleep 2s

Hide
Set TypingSpeed 1ms
Type `rm .mlclient/mlclient-qa.yaml; printf '\033[1A\033[2K\r'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env copy dev qa --edit"
Enter
Wait+Screen /host: dev.example.com/
Sleep 2s
Type "2j0wwce"
Type "qa"
Escape
Sleep 1s
Type ":wq"
Enter
Wait
Sleep 2s
