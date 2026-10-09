#!/usr/bin/env bash
set -euo pipefail

unit=false
integration=false
lint=false
docs=false
while IFS= read -r -d '' path; do
  case "$path" in
    docs/*|mkdocs.yml|scripts/check_docs.py)
      docs=true ;;
    README.md|LICENSE|.gitignore|meta/*)
      ;;
    mlclient/*)
      unit=true; integration=true; lint=true; docs=true ;;
    tests/unit/*)
      unit=true; lint=true ;;
    tests/integration/*)
      integration=true; lint=true ;;
    tests/*)
      unit=true; integration=true; lint=true ;;
    *)
      # Unknown build/configuration inputs require all checks.
      unit=true; integration=true; lint=true; docs=true ;;
  esac
done
printf 'unit=%s\nintegration=%s\nlint=%s\ndocs=%s\n' "$unit" "$integration" "$lint" "$docs"
