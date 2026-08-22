#!/bin/bash
# Every module with a `main()`, enumerated from the filesystem.
#
#  A HAND-WRITTEN LIST HID TWO REGRESSIONS. There are ~30 modules with a
# main() and every sweep in one session used a list of a dozen; `ugm.practice`
# was red for two commits and `ugm.attention` for six before either was noticed.
# Pick nothing: ask the filesystem.
#
#  AND THE GLOB WAS `ugm/*.py`, WHICH IS THE SAME BUG ONE LEVEL UP. The
# moment the tree grew `core/`, `learning/`, `gates/` and `probes/`, a flat glob
# would have quietly stopped covering every module that moved -- reporting
# green because it had stopped looking. `find` recurses; nothing here names a
# directory either.
#
#  AND THE TEST WAS `^def main`, WHICH IS THE SAME BUG A THIRD TIME. Two of
# the §20 floor gates -- `gates.agreement` and `gates.quiescence` -- name their
# entry point `run`, so a grep for `main` walked past both. Neither has ever
# been in a sweep, and `agreement` was broken by the locus cut with nothing to
# say so. The question is not what the function is CALLED: it is whether the
# module is a door, and `if __name__ == "__main__"` is what says that.
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
  grep -q '^if __name__ == "__main__":' "$f" || continue
  mod=$(echo "${f%.py}" | tr '/' '.')
  ran=$((ran+1))
  timeout 900 python3 -m "$mod" >"/tmp/sweep.$base.out" 2>&1
  rc=$?
  [ $rc -eq 0 ] || { echo "  $mod exit=$rc   (/tmp/sweep.$base.out)"; fail=$((fail+1)); }
done
echo "  ---- $fail failing, $ran run"
