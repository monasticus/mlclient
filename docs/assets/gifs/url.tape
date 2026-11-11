Output "docs/assets/gifs/url.gif"
Require ml

Set Shell "bash"
Set Width 1000
Set Height 660
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
Type `unset NO_COLOR HISTIGNORE HISTCONTROL; HISTFILE=/dev/null; set -o history; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; mkdir .mlclient; printf 'host: ml-dev.example.com\n' > .mlclient/mlclient-dev.yaml; printf 'host: ml-qa.example.com\n' > .mlclient/mlclient-qa.yaml; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml url -e dev`
Enter
Wait
Sleep 3s
Type "ml url admin -e dev -e qa"
Enter
Wait
Wait+Screen /dev.*qa/
Sleep 4s
Type `ml url admin -e dev --open`
Enter
Wait
Sleep 3s
