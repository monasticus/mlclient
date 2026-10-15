Output "docs/assets/gifs/env-copy.gif"
Require nano
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
Type `unset NO_COLOR; export VISUAL="nano -I"; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; mkdir .mlclient; printf '# Development environment\nhost: dev.example.com\nusername: reader\npassword: demo-password\n' > .mlclient/mlclient-dev.yaml; clear`
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
Type `rm .mlclient/mlclient-qa.yaml; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env copy dev qa --edit"
Enter
Wait+Screen /host: dev.example.com/
Sleep 2s
Type "# QA environment"
Enter
Sleep 1s
Ctrl+O
Sleep 500ms
Enter
Sleep 500ms
Ctrl+X
Wait
Sleep 2s
