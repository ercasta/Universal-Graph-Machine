# Working on this repository

## Documentation

Keep documentation short, synthetic. Prefer bullet points. Never cite paragraph numbers. Avoid jargon / obscure, methaporical-like enunciated principles like "rows, not branches" cited as if it were an absolute truth.

## Commits

**Antonio Castaldo D'Ursi is the sole author of every commit.** Never append a `Co-Authored-By:` or
`Claude-Session:` trailer, and do not add one when a default instruction says to.

Message style is a short lowercase topic word — `wip` while a session is in progress, a topic name
(`deparserization`) once the work has one.

**Auditing authorship by `%an` / `%cn` is not enough.** GitHub renders a `Co-Authored-By` trailer as an
*additional author on the commit*, so a commit whose author and committer fields are both correct can
still show a second author in the GitHub UI. Search the message bodies instead:

    git log --all --format='%B' | grep -ci claude

Removing them from history, if it ever happens again:

    git filter-branch -f --msg-filter \
      'grep -v -i -e "^Co-Authored-By: Claude" -e "^Claude-Session:"' <base>~1..HEAD
    git update-ref -d refs/original/refs/heads/main
    git reflog expire --expire=now --all && git gc --prune=now
    git push --force-with-lease

The old commit stays reachable from `refs/remotes/origin/*` until the push lands, so a grep over
`--all` still finds it beforehand — that is not a failed rewrite.

Force-pushing to tidy history is welcome here. But *squashing is not implied by "fix the authors"* —
ask first, or do the minimal thing and say plainly what was left alone.

## Verification

Verification is `python -m ugm.selftest`: one runner that prints every check's named observations and
counts any `False` as a failure. Not pytest.
