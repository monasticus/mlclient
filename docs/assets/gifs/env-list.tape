Output "docs/assets/gifs/env-list.gif"
Require ml

Set Shell "bash"
Set Width 1000
Set Height 380
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
Type `unset NO_COLOR; demo_dir=$(mktemp -d /tmp/ml-list-demo.XXXXXX); export HOME="$demo_dir/home"; mkdir -p "$HOME/.mlclient" "$demo_dir/project/.mlclient"; cd "$demo_dir/project"; trap 'rm -rf "$demo_dir"' EXIT; for name in local staging qa; do printf 'host: localhost\n' > ".mlclient/mlclient-$name.yaml"; done; for name in local production; do printf 'host: localhost\n' > "$HOME/.mlclient/mlclient-$name.yaml"; done; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env list"
Enter
Wait
Wait+Screen /staging/
Sleep 2s

Type "ml env list --global"
Enter
Wait
Wait+Screen /production/
Sleep 4s
