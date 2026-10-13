Output "docs/assets/gifs/http-pretty.gif"
Require ml
Require curl

Set Shell "bash"
Set Width 900
Set Height 440
Set Theme "Gruvbox Light"
Set FontFamily "JetBrains Mono"
Set FontSize 16
Set Padding 30
Set BorderRadius 10
Set Margin 0
Set LetterSpacing 1
Set LineHeight 1.2
Set CursorBlink true
Set TypingSpeed 50ms

Hide
Set TypingSpeed 1ms
Type `unset NO_COLOR HISTIGNORE HISTCONTROL; HISTSIZE=100; HISTFILE=/dev/null; set -o history; demo_dir=$(mktemp -d /tmp/mlclient-demo.XXXXXX); cd "$demo_dir"`
Enter
Wait
Type `mkdir .mlclient; printf 'host: ml-dev.172.22.0.2.nip.io\nusername: admin\npassword: admin\nauth: digest\nprotocol: http\n' > .mlclient/mlclient-local.yaml`
Enter
Wait
Type `test "$(curl --silent --digest -u admin:admin -o /dev/null -w '%{http_code}' 'http://ml-dev.172.22.0.2.nip.io:8000/v1/documents?uri=/vhs-demo.xml')" = 404 || exit 1`
Enter
Wait
Type `trap 'ml http delete /v1/documents uri=/vhs-demo.xml; rm -rf "$demo_dir"' EXIT`
Enter
Wait
Type `ml http put /v1/documents uri=/vhs-demo.xml Content-Type:application/xml -b '<order id="42"><customer>Ada</customer><total currency="EUR">29.90</total></order>'`
Enter
Wait
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml http get /v1/documents uri=/vhs-demo.xml"
Enter
Wait
Wait+Screen /<order id="42">/
Sleep 2s
Up
Sleep 500ms
Type " --pretty"
Enter
Wait
Wait+Screen /(?m)^  /
Sleep 3s

Hide
Set TypingSpeed 1ms
Type "clear"
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml http get /manage/v2/users/nobody/properties -c manage format=json"
Enter
Wait
Wait+Screen /user-name/
Sleep 2s
Up
Sleep 500ms
Type " --pretty"
Enter
Wait
Wait+Screen /(?m)^  /
Sleep 3s

Hide
Set TypingSpeed 1ms
Type "ml http delete /v1/documents uri=/vhs-demo.xml"
Enter
Wait
Type `trap - EXIT; cd /tmp; rm -rf "$demo_dir"`
Enter
Wait
Sleep 100ms
