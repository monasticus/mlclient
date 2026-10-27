Output "docs/assets/gifs/trace-events.gif"
Require ml
Require docker
# Server prerequisites and restoration: fixtures/README.txt

Set Shell "bash"
Set Width 860
Set Height 540
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
Type `unset NO_COLOR HISTIGNORE HISTCONTROL; HISTFILE=/dev/null; set -o history; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; mkdir .mlclient; cluster_host=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ml_cluster_node1); dev_host=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mlclient_cts_query_12); printf 'host: %s\nusername: admin\npassword: admin\napp-servers:\n  - id: app\n    port: 8010\n    rest: true\n' "$cluster_host" > .mlclient/mlclient-local.yaml; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml trace-events`
Enter
Wait
Sleep 2s
Type `ml trace-events off`
Enter
Wait
Sleep 2s
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml trace-events -E "Optic Query Parsing" on`
Enter
Wait
Sleep 2s
Type `ml trace-events -E "XDMP Deadlock" on`
Enter
Wait
Sleep 2s
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type "ml trace-events -i"
Enter
Wait+Screen /Trace events/
Sleep 2s
Space
Sleep 1s
Down
Space
Sleep 1300ms
Down
Space
Sleep 2s
Enter
Wait
Sleep 4s
