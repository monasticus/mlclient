Output "docs/assets/gifs/log-level.gif"
Require ml
Require docker
# Server prerequisites and restoration: fixtures/README.txt

Set Shell "bash"
Set Width 800
Set Height 560
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
Type `ml log-level finest`
Enter
Wait
Sleep 1200ms
Type `ml log-level finer`
Enter
Wait
Sleep 1200ms
Type `ml log-level fine`
Enter
Wait
Sleep 1200ms
Type `ml log-level debug`
Enter
Wait
Sleep 1200ms
Type `ml log-level config`
Enter
Wait
Sleep 1200ms
Type `ml log-level info`
Enter
Wait
Sleep 1200ms
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml log-level notice`
Enter
Wait
Sleep 1200ms
Type `ml log-level warning`
Enter
Wait
Sleep 1200ms
Type `ml log-level error`
Enter
Wait
Sleep 1200ms
Type `ml log-level critical`
Enter
Wait
Sleep 1200ms
Type `ml log-level alert`
Enter
Wait
Sleep 1200ms
Type `ml log-level emergency`
Enter
Wait
Sleep 1200ms
Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml log-level`
Enter
Wait
Sleep 2s
Type `ml log-level -s vhs-bookstore`
Enter
Wait
Sleep 2s
Type `ml log-level -t system`
Enter
Wait
Sleep 3s
