Output "docs/assets/gifs/invoke.gif"
Require ml

Set Shell "bash"
Set Width 1060
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

# Uses disposable vhs-docs-demo REST instances on localhost:18008 and :18009.

Hide
Set TypingSpeed 1ms
Type `unset NO_COLOR HISTIGNORE HISTCONTROL; HISTSIZE=100; HISTFILE=/dev/null; set -o history; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; mkdir .mlclient; printf 'host: localhost\nusername: admin\npassword: admin\napp-servers:\n  - id: app-services\n    port: 18008\n    rest: true\n' > .mlclient/mlclient-local.yaml; cp .mlclient/mlclient-local.yaml .mlclient/mlclient-dev.yaml; sed s/18008/18009/ .mlclient/mlclient-local.yaml > .mlclient/mlclient-qa.yaml`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Hide
Set TypingSpeed 1ms
Type `test "$(ml eval -d vhs-docs-demo-modules -x 'empty((doc("/ext/mlclient-demo/greeting.xqy"), doc("/ext/monthly-report.sjs")))' | tail -n 1)" = true || exit 1`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Hide
Set TypingSpeed 1ms
Type `cleanup() { for uri in /ext/mlclient-demo/greeting.xqy /ext/monthly-report.sjs; do ml http delete /v1/documents database=vhs-docs-demo-modules uri="$uri" >/dev/null; done; ml http delete /v1/documents -e qa database=vhs-docs-qa-modules uri=/ext/monthly-report.sjs >/dev/null; rm -rf "$demo_dir"; }; trap cleanup EXIT`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Hide
Set TypingSpeed 1ms
Type `ml http put /v1/documents database=vhs-docs-demo-modules uri=/ext/mlclient-demo/greeting.xqy Content-Type:application/xquery -b 'xquery version "1.0-ml"; declare variable $name external; <greeting><name>{$name}</name><message>Hello, {$name}!</message></greeting>'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Hide
Set TypingSpeed 1ms
Type `ml http put /v1/documents database=vhs-docs-demo-modules uri=/ext/monthly-report.sjs Content-Type:application/javascript -b '({month: month, sales: {orders: 24, revenue: "718.00"}, currency: "EUR"})'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
Hide
Set TypingSpeed 1ms
Type `ml http put /v1/documents -e qa database=vhs-docs-qa-modules uri=/ext/monthly-report.sjs Content-Type:application/javascript -b '({month: month, orders: 24, revenue: "718.00", currency: "EUR"})'`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml invoke /ext/mlclient-demo/greeting.xqy --var name=Ada"
Enter
Wait
Wait+Screen /<message>Hello, Ada!<\/message>/
Sleep 3s
Up
Ctrl+W
Type "name=Tom"
Enter
Wait
Wait+Screen /<message>Hello, Tom!<\/message>/
Sleep 3s

Hide
Set TypingSpeed 1ms
Type `clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml invoke /ext/monthly-report.sjs -e dev -e qa --var month=2026-10"
Enter
Wait
Wait+Screen /sales/
Sleep 5s

Hide
Set TypingSpeed 1ms
Type `cleanup; trap - EXIT`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show
