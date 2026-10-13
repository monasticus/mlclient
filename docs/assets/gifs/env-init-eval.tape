Output "docs/assets/gifs/env-init-eval.gif"
Require ml

Set Shell "bash"
Set Width 800
Set Height 380
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
Type `unset NO_COLOR; demo_dir=$(mktemp -d /tmp/mlclient-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT`
Enter
Wait
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env init local"
Enter
Wait
Wait+Screen /Created/
Sleep 1s

Type `ml eval -x '"Hello World!"'`
Enter
Wait
Wait+Screen /Hello World!/
Sleep 3s

Type `ml eval -j 'fn.currentDateTime()'`
Enter
Wait
Wait+Screen /[0-9]{4}-[0-9]{2}-[0-9]{2}T/
Sleep 3s
