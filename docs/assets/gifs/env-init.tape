Output "docs/assets/gifs/env-init.gif"
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
Type `unset NO_COLOR; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; printf 'mlHost=ml.example.com\nmlUsername=reader\nmlPassword=demo-password\n' > gradle.properties; printf 'mlAppName=bookstore\nmlRestPort=8010\n' > gradle-dev.properties; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env init local"
Enter
Wait
Wait+Screen /mlclient-local.yaml/
Sleep 2s

Type "ml env init --from-gradle=dev"
Enter
Wait
Wait+Screen /mlclient-dev.yaml/
Sleep 2s

Type "ml env init server --from-host=localhost:18002"
Enter
Wait
Wait+Screen /mlclient-server.yaml/
Sleep 3s

Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env init"
Enter
Wait+Screen /Environment name:/
Sleep 1s
Type "qa"
Enter
Wait+Screen /Source/
Sleep 1s
Type "2"
Enter
Wait+Screen /Protocol/
Enter
Wait+Screen /Host/
Enter
Wait+Screen /Port/
Type "18002"
Enter
Wait+Screen /Username/
Enter
Wait+Screen /Password/
Enter
Sleep 500ms
Enter
Wait
Sleep 4s
