Output "docs/assets/gifs/env-edit.gif"
Require nano
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
Type `unset NO_COLOR; export VISUAL="nano -I"; demo_dir=$(mktemp -d /tmp/ml-demo.XXXXXX); cd "$demo_dir"; global_dir="$HOME/.mlclient"; global_file="$global_dir/mlclient-dev.yaml"; global_dir_existed=no; test ! -d "$global_dir" || global_dir_existed=yes; mkdir -p "$global_dir" .mlclient; if test -e "$global_file" || test -L "$global_file"; then mv -- "$global_file" "$demo_dir/global-dev-backup"; fi; trap 'rm -f "$global_file"; if test -e "$demo_dir/global-dev-backup" || test -L "$demo_dir/global-dev-backup"; then mv -- "$demo_dir/global-dev-backup" "$global_file"; fi; if test "$global_dir_existed" = no; then rmdir "$global_dir" 2>/dev/null || true; fi; rm -rf "$demo_dir"' EXIT; printf '# Local environment\nhost: localhost\nusername: admin\npassword: admin\n' > .mlclient/mlclient-local.yaml; printf '# Global development environment\nhost: ml.example.com\nusername: reader\npassword: demo-password\n' > "$global_file"; clear`
Enter
Wait
Sleep 500ms
Set TypingSpeed 50ms
Show

Type "ml env edit local"
Enter
Wait+Screen /host: localhost/
Sleep 2s
Type "# Local development"
Enter
Sleep 1s
Ctrl+O
Sleep 500ms
Enter
Sleep 500ms
Ctrl+X
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

Type "ml env edit dev --global"
Enter
Wait+Screen /host: ml.example.com/
Sleep 2s
Type "# Shared development"
Enter
Sleep 1s
Ctrl+O
Sleep 500ms
Enter
Sleep 500ms
Ctrl+X
Wait
Sleep 2s
