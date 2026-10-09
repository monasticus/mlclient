#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
check() {
  local expected="$1"
  shift
  local actual
  actual=$(printf '%s\0' "$@" | bash .github/scripts/select-checks.sh)
  [[ "$actual" == "$expected" ]] || {
    printf 'Unexpected checks for %s:\n%s\n' "$*" "$actual" >&2
    exit 1
  }
}
none=$'unit=false\nintegration=false\nlint=false\ndocs=false'
docs=$'unit=false\nintegration=false\nlint=false\ndocs=true'
unit=$'unit=true\nintegration=false\nlint=true\ndocs=false'
integration=$'unit=false\nintegration=true\nlint=true\ndocs=false'
tests=$'unit=true\nintegration=true\nlint=true\ndocs=false'
all=$'unit=true\nintegration=true\nlint=true\ndocs=true'
check "$none" README.md LICENSE meta/review.md
check "$docs" docs/user/python/search.md docs/examples/custom_expression.py mkdocs.yml scripts/check_docs.py
check "$unit" tests/unit/test_example.py
check "$integration" tests/integration/docker-compose.yaml
check "$tests" tests/utils/resources.py tests/resources/example.json
check "$all" mlclient/search/options.py docs/user/python/search.md
check "$all" pyproject.toml
check "$all" poetry.lock
check "$all" Makefile
check "$all" .github/workflows/unit-test.yml
check "$all" unknown-file
[[ $(bash .github/scripts/select-checks.sh < /dev/null) == "$none" ]]
printf 'Check selection scenarios passed.\n'
