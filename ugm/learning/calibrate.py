"""Run episodes, score them, and search the attention numbers.

The judge lives in the episode and is ordinary rules, so it is subject to
everything else the loop does -- including attention gating. That is the one
place this could quietly lie to itself: a calibration that starved its own
judge would leave no verdict, and *no verdict counted as success* would score
that as the best run of all. So the absence of a verdict is a FAILURE, and a
judge that never got a turn is a calibration that did not work.
"""

import random
import re
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.machine import Machine
from ..core.text import ParseError, load

#: What a judge concludes. `succeeded` is the verdict; `score(n)` is optional
#: and lets an episode say *how well* rather than only *whether*.
SUCCEEDED = "succeeded"
SCORE = "score"


class Episode:
    """One `.ugm` file: the starting condition and the judge, together."""

    def __init__(self, path: str, limit: int = 200) -> None:
        self.path = path
        self.limit = limit
        with open(path, "r", encoding="utf-8") as fh:
            self.source = fh.read()

    def __repr__(self) -> str:
        return f"Episode({self.path!r})"


def run_episode(corpus: str, episode: Episode,
                register=None) -> Tuple[bool, float, str]:
    """`(succeeded, score, why)` for one corpus text against one episode.

    The corpus is TEXT rather than a path, because a calibration run holds a
    mutated corpus that was never written to disk -- and writing every
    candidate out to score it would make the search a filesystem benchmark.
    """
    m = Machine()
    ldr = load(m, "", scope="episode")
    if register is not None:
        register(ldr)
    try:
        ldr.load(corpus)
        ldr.load(episode.source)
    except ParseError as e:
        # A mutation that will not parse is a failed candidate, not a crash:
        # the search is allowed to propose nonsense as long as it is told.
        return False, 0.0, f"parse: {e}"
    m.run(limit=episode.limit)
    believed = {m.g.show(p) for p in m.pad.believed()}
    ok = SUCCEEDED in believed
    score = 0.0
    for shown in believed:
        got = re.fullmatch(re.escape(SCORE) + r"\((-?\d+)\)", shown)
        if got:
            score = max(score, float(got.group(1)))
    if not ok and score == 0.0:
        return False, 0.0, "no verdict"
    return ok, score, "ok"


# -- the numbers, and only the numbers ---------------------------------------

#: A bracketed line contribution: `[+3, attention_multiplier:1.2]`.
_BRACKET = re.compile(
    r"\[\s*([+-]?\d+)\s*(?:,\s*attention_multiplier\s*:\s*(\d+(?:\.\d+)?)\s*)?\]")
#: An `attend` tail: `attend($x, 5, 2, 1, 9)`.
_ATTEND = re.compile(r"(attend\(\s*[^,)]+)((?:\s*,\s*\d+)+)(\s*\))")


def numbers(text: str) -> List[Tuple[int, int, str]]:
    """Every number a mutator may touch, as `(start, end, kind)` spans.

    Spans rather than a parsed model on purpose: the tuned corpus is the
    original text with the corrections in it, so a calibration that rewrote
    the file through a parser would hand back something the author did not
    write and could not diff.
    """
    out = []
    for got in _BRACKET.finditer(text):
        out.append((got.start(1), got.end(1), "contribution"))
        if got.group(2) is not None:
            out.append((got.start(2), got.end(2), "multiplier"))
    for got in _ATTEND.finditer(text):
        for num in re.finditer(r"\d+", got.group(2)):
            base = got.start(2)
            out.append((base + num.start(), base + num.end(), "attend"))
    return sorted(out)


def _nudge(value: str, kind: str, rng: random.Random) -> str:
    if kind == "multiplier":
        got = max(0.0, float(value) + rng.choice((-0.5, -0.2, 0.2, 0.5)))
        return f"{got:g}"
    got = int(value) + rng.choice((-2, -1, 1, 2))
    if kind == "attend":
        got = max(0, got)          # a lifespan below zero is not a claim
    return str(got)


def mutate(text: str, rng: random.Random, n: int = 1) -> str:
    """`n` numbers changed, and nothing else. Rules are not touched.

    ⚠ NOT YET IN THE SEARCH SPACE, and it will have to be: a GATE. Under
    consumption, two rules are ordered by their data dependency and by
    nothing else -- so where a corpus needs one to run before another and
    neither reads what the other writes, there is nothing to order them. The
    fix is a synthetic proposition, `gate#12322` or the like, produced by one
    rule's right-hand side and keyed on by the other's left. A mutator that
    could introduce one would be changing STRUCTURE rather than numbers,
    which is why it is out of this phase and written here rather than built:
    the moment mutators may add a line, they may also add a line that makes
    a corpus unreadable, and that wants deciding before it is possible.
    """
    spans = numbers(text)
    if not spans:
        return text
    for start, end, kind in sorted(rng.sample(spans, min(n, len(spans))),
                                   reverse=True):
        text = text[:start] + _nudge(text[start:end], kind, rng) + text[end:]
    return text


def fitness(corpus: str, episodes: Sequence[Episode], register=None) -> float:
    """Summed over episodes. A failure scores nothing at all rather than a
    little, so a candidate cannot buy a lost episode with a won one."""
    total = 0.0
    for ep in episodes:
        ok, score, _why = run_episode(corpus, ep, register)
        if not ok:
            continue
        total += 1.0 + score
    return total


def calibrate(corpus: str, episodes: Sequence[Episode], rounds: int = 20,
              population: int = 8, seed: int = 0,
              register=None) -> Tuple[str, float, List[float]]:
    """`(best_text, best_fitness, history)`.

    Evolutionary in the plainest sense -- a population, mutation, keep the
    best -- and no crossover, because two calibrations of one corpus differ
    at scattered numbers and splicing them produces a third that neither
    parent's episodes ever justified.

    ⚠ Nothing here guards against overfitting. The best calibration is the
    one that wins THESE episodes, and there is no held-out set. Deliberate
    for now, and it means a result is a claim about the episodes and not yet
    about the corpus.
    """
    rng = random.Random(seed)
    best, best_fit = corpus, fitness(corpus, episodes, register)
    history = [best_fit]
    for _ in range(rounds):
        challengers = [mutate(best, rng, rng.choice((1, 1, 2)))
                       for _ in range(population)]
        for cand in challengers:
            got = fitness(cand, episodes, register)
            if got > best_fit:
                best, best_fit = cand, got
        history.append(best_fit)
    return best, best_fit, history
