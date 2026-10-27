Output "docs/assets/gifs/url.gif"
Require ml
Require docker

Set Shell "bash"
Set Width 1000
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
Type `unset NO_COLOR HISTIGNORE HISTCONTROL; HISTFILE=/dev/null; set -o history; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; trap 'rm -rf "$demo_dir"' EXIT; mkdir .mlclient; cluster_host=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ml_cluster_node1); dev_host=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mlclient_cts_query_12); printf 'host: ml-dev.%s.nip.io\nusername: admin\npassword: admin\n' "$dev_host" > .mlclient/mlclient-dev.yaml; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Type `ml url -e dev`
Enter
Wait
Sleep 3s
Type `ml url admin -e dev --open`
Enter
Wait
Sleep 3s
