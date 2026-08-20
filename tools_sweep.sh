#!/bin/bash
# Every module with a `main()`, enumerated from the filesystem.
#
# ⚠⚠⚠ A HAND-WRITTEN LIST HID TWO REGRESSIONS. There are ~30 modules with a
# main() and every sweep in one session used a list of a dozen; `ugm.practice`
# was red for two commits and `ugm.attention` for six before either was noticed.
# Pick nothing: ask the filesystem.
#
#   ./tools_sweep.sh          everything but `necessity` (which takes >10 min)
#   ./tools_sweep.sh --all    everything
cd "$(dirname "$0")"
skip="__init__ __main__ selftest"
[ "$1" = "--all" ] || skip="$skip necessity"
fail=0
for f in ugm/*.py; do
  m=$(basename "$f" .py)
  case " $skip " in *" $m "*) continue;; esac
  grep -q "^def main" "$f" || continue
  timeout 900 python3 -m "ugm.$m" >"/tmp/sweep.$m.out" 2>&1
  rc=$?
  [ $rc -eq 0 ] || { echo "  $m exit=$rc   (/tmp/sweep.$m.out)"; fail=$((fail+1)); }
done
echo "  ---- $fail failing"
