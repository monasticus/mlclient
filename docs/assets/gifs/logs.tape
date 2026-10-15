Output "docs/assets/gifs/logs.gif"
Require ml
Require docker
# Server prerequisites and restoration: fixtures/README.txt

Set Shell "bash"
Set Width 1000
Set Height 600
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

# Requires the three nodes in dev/docker-compose.yaml and the demo REST
# App Server vhs-bookstore on port 8010 with INFO log entries on each node.
# Container addresses are discovered at render time; set --from to the seed time.
Hide
Set TypingSpeed 1ms
Type `unset NO_COLOR; demo_dir=$(mktemp -d /tmp/mlclient-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT`
Enter
Wait
Type `cluster_host=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ml_cluster_node1); mkdir .mlclient; printf 'host: %s\nusername: admin\npassword: admin\nauth: digest\nprotocol: http\napp-servers:\n  - id: app\n    port: 8010\n    rest: true\n' "$cluster_host" > .mlclient/mlclient-local.yaml`
Enter
Wait
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type `ml logs -s app --from 17:00 --regex "Bookstore: request"`
Enter
Wait
Wait+Screen /Bookstore:/
Sleep 3s

Hide
Set TypingSpeed 1ms
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type `ml logs -s 8010 --all-hosts --from 17:00 --regex 'Bookstore: request'`
Enter
Wait
Wait+Screen /ml_cluster_node1/
Wait+Screen /ml_cluster_node2/
Wait+Screen /ml_cluster_node3/
Sleep 4s

Hide
Set TypingSpeed 1ms
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type "ml logs -s app --log-type access | tail -n 6"
Enter
Wait
Sleep 4s

Hide
Set TypingSpeed 1ms
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type "ml logs -s 8011 --log-type request"
Enter
Wait
Sleep 4s
