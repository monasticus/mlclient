Output "docs/assets/gifs/cluster-logs.gif"
Require ml

Set Shell "bash"
Set Width 900
Set Height 520
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
# Local container IP may change; update the hidden environment when needed.
Hide
Set TypingSpeed 1ms
Type `unset NO_COLOR; demo_dir=$(mktemp -d /tmp/mlclient-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT`
Enter
Wait
Type `mkdir .mlclient; printf 'host: 172.19.0.3\nusername: admin\npassword: admin\nauth: digest\nprotocol: http\napp-servers:\n  - id: app\n    port: 8010\n    rest: true\n' > .mlclient/mlclient-local.yaml`
Enter
Wait
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type `ml logs -s app --regex "Bookstore: request"`
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

Type `ml logs -s 8010 --all-hosts --regex 'Bookstore: request'`
Enter
Wait
Wait+Screen /ml_cluster_node1/
Wait+Screen /ml_cluster_node2/
Wait+Screen /ml_cluster_node3/
Sleep 4s
