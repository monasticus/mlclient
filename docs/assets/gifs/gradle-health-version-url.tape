Output "docs/assets/gifs/gradle-health-version-url.gif"
Require ml
# Demo hostname points to the MarkLogic 12 container; update if its IP changes.

Set Shell "bash"
Set Width 880
Set Height 620
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
Type `unset NO_COLOR; demo_dir=$(mktemp -d /tmp/mlclient-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT`
Enter
Wait
Type `printf 'mlHost=ml-dev.172.22.0.2.nip.io\nmlUsername=admin\nmlPassword=admin\n' > gradle.properties; printf 'mlAppName=demo\n' > gradle-dev.properties`
Enter
Wait
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env init --from-gradle=dev"
Enter
Wait
Wait+Screen /Created/
Sleep 1s

Type "ml health -e dev"
Enter
Wait
Wait+Screen /HEALTHY/
Sleep 1s

Type "ml version -e dev"
Enter
Wait
Wait+Screen /12\.1\.0/
Sleep 1s

Type "ml url -e dev"
Enter
Wait
Sleep 3s

Type "ml url -e dev qc --open"
Enter
Wait
Wait+Screen /Opened in browser/
Sleep 3s
