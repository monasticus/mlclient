Output "docs/assets/gifs/health.gif"
Require ml
Require docker
# Server prerequisites and restoration: fixtures/README.txt

Set Shell "bash"
Set Width 860
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
Type `unset NO_COLOR HISTIGNORE HISTCONTROL; HISTFILE=/dev/null; set -o history; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; mkdir .mlclient; cluster_host=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ml_cluster_node1); dev_host=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mlclient_cts_query_12); printf 'host: ml-dev.%s.nip.io\nusername: admin\npassword: admin\n' "$dev_host" > .mlclient/mlclient-dev.yaml; printf 'host: %s\napp-servers:\n  - id: health\n    port: 8011\n    auth: app\n' "$cluster_host" > .mlclient/mlclient-qa.yaml; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml health -e dev`
Enter
Wait
Sleep 2s
Type "ml health -e qa --watch -i 1"
Enter
Wait+Screen /UNHEALTHY/
Sleep 3500ms
Ctrl+C
Wait
Sleep 1s
Up
Backspace
Type "2 -o --lines 5"
Enter
# The isolated MarkLogic endpoint returns 503 for eight probes, then 200.
Sleep 12s
Ctrl+C
Wait
Sleep 2s
