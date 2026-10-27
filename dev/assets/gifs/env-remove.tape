Output "docs/assets/gifs/env-remove.gif"
Require ml

Set Shell "bash"
Set Width 940
Set Height 300
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
Type `unset NO_COLOR WAYLAND_DISPLAY; demo_dir=$(mktemp -d /tmp/XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; mkdir .mlclient; printf 'host: dev.example.com\n' > .mlclient/mlclient-dev.yaml; printf 'host: qa.example.com\n' > .mlclient/mlclient-qa.yaml; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env remove dev"
Enter
Wait+Screen /Remove environment dev/
Sleep 1s
Type "y"
Enter
Wait
Wait+Screen /Removed/
Sleep 2s

Type "ml env remove qa --force"
Enter
Wait
Wait+Screen /mlclient-qa.yaml/
Sleep 3s
