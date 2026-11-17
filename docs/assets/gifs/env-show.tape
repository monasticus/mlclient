Output "docs/assets/gifs/env-show.gif"
Require xclip
# Render with a working clipboard session; an isolated X server avoids changing the desktop clipboard.
Require ml

Set Shell "bash"
Set Width 800
Set Height 580
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
Type `unset NO_COLOR WAYLAND_DISPLAY; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; mkdir .mlclient; printf 'app-name: bookstore\nprotocol: http\nhost: localhost\nusername: reader\npassword: demo-password\nauth: digest\napp-servers:\n  - id: app-services\n    port: 8000\n    rest: true\n  - id: bookstore\n    port: 8010\n    rest: true\n' > .mlclient/mlclient-local.yaml; cp .mlclient/mlclient-local.yaml .mlclient/mlclient-staging.yaml; sed -i 's/bookstore/bookstore-staging/g' .mlclient/mlclient-staging.yaml; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env show"
Enter
Wait
Wait+Screen /bookstore/
Sleep 3s

Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env show -e staging"
Enter
Wait
Wait+Screen /bookstore-staging/
Sleep 3s

Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env show -e staging --raw"
Enter
Wait
Wait+Screen /demo-password/
Sleep 3s

Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env show host"
Enter
Wait
Wait+Screen /localhost/
Sleep 2s

Type "ml env show password --copy"
Enter
Wait
Wait+Screen /Copied to clipboard/
Sleep 3s
