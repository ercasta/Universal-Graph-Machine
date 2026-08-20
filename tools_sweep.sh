#!/bin/bash
# Every module with a `main()`, enumerated from the filesystem.
#
# ⚠⚠⚠ A HAND-WRITTEN LIST HID TWO REGRESSIONS. There are ~30 modules with a
# main() and every sweep in one session used a list of a dozen; `ugm.practice`
# was red for two commits and `ugm.attention` for six before either was noticed.
# Pick nothing: ask the filesystem.
#
# ⚠⚠⚠ AND THE GLOB WAS `ugm/*.py`, WHICH IS THE SAME BUG ONE LEVEL UP. The
# moment the tree grew `core/`, `learning/`, `gates/` and `probes/`, a flat glob
# would have quietly stopped covering every module that moved -- reporting
# green because it had stopped looking. `find` recurses; nothing here names a
# directory either.
#
#   ./tools_sweep.sh          everything but `necessity` (which takes >10 min)
#   ./tools_sweep.sh --all    everything
cd "$(dirname "$0")"
skip="__init__ __main__ selftest"
[ "$1" = "--all" ] || skip="$skip necessity"
fail=0
ran=0
for f in $(find ugm -name '*.py' | sort); do
  base=$(basename "$f" .py)
  case " $skip " in *" $base "*) continue;; esac
  grep -q "^def main" "$f" || continue
  mod=$(echo "${f%.py}" | tr '/' '.')
  ran=$((ran+1))
  timeout 900 python3 -m "$mod" >"/tmp/sweep.$base.out" 2>&1
  rc=$?
  [ $rc -eq 0 ] || { echo "  $mod exit=$rc   (/tmp/sweep.$base.out)"; fail=$((fail+1)); }
done
echo "  ---- $fail failing, $ran run"
