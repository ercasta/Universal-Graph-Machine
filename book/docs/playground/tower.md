# Watch it plan — live

This is the real engine, running **in your browser**. Nothing is sent to a
server — it's loaded onto your device the first time you press **Run** (that
first load takes a few seconds; after that it's instant).

The world is Chapter 0's: three crates, `a`, `b` and `c`, all on the ground. The
machine can **stack** one clear crate on another, **unstack** one onto the
ground, or **paint** one red.

Write what you want to be true. Press **Run** and watch it think:

- **⛔ Refused** — a move a `never` line ruled out. It was *not* imagined.
- **· Considering** — a move it ranked. Band 4 means "writes exactly what's
  missing"; band 0 means "nothing to do with the goal".
- **◐ Imagined** — a move it actually tried, and what's still open afterwards.
- **✔ Plan found** — and then it carries the plan out for real.

<div class="ugm-playground"
     data-wheel="../wheels/universal_graph_machine-0.2.0-py3-none-any.whl"
     data-mode="plan">

  <label class="ugm-label" for="ugm-goal">What must be true</label>
  <textarea id="ugm-goal" class="ugm-corpus" spellcheck="false" rows="5">
goal build a tower:
    a on b
    b on c
    never paint
</textarea>

  <div class="ugm-controls">
    <button class="ugm-run" type="button">Run</button>
  </div>

  <div class="ugm-quick">
    <span class="ugm-quick-label">Try:</span>
    <button class="ugm-ask" type="button"
            data-text="goal build a tower:&#10;    a on b&#10;    b on c">without the ban</button>
    <button class="ugm-ask" type="button"
            data-text="goal a short tower:&#10;    a on b&#10;    b on c&#10;    at most 1 steps">a budget of one</button>
    <button class="ugm-ask" type="button"
            data-text="goal impossible:&#10;    a on b&#10;    b on c&#10;    never stack">ban the only useful move</button>
    <button class="ugm-ask" type="button"
            data-text="goal paint it:&#10;    a on b&#10;    must paint">insist on painting</button>
  </div>

  <div class="ugm-steps"></div>
</div>

## Things worth trying

**Delete `never paint` and run again.** Nothing else changes — but now you'll
see the machine *consider* painting, at band 0, because it has nothing to do
with any open constraint. With the ban in place those moves never appear at all.
That's the difference between ranking and pruning, from Chapter 7.

**Give it a budget it can't meet.** `at most 1 steps` on a two-step goal fails
honestly, and the reason names both halves: what was still wanted, *and* that 78
actions were ruled out by the budget. It doesn't just say no.

**Ban the only useful move.** `never stack` makes the tower unreachable — but
watch what actually happens, because it isn't what you'd guess. The machine
keeps going for a long time (around 146 events, 48 of them refusals), because
`unstack` is still allowed and there are plenty of pointless worlds to wander
into. Pruning makes each forbidden move free; it does **not** make a hopeless
search short. Cheap per move is not the same as quick overall.

**Make it do something pointless.** `must paint` is a *liveness* constraint: the
plan isn't finished until it has painted something, even though painting does
nothing for the goal. Compare where `paint` lands in the plan.

!!! note "The animation is the real run"
    These cards come from the engine's own trace hook, and the engine's self-test
    asserts that a traced search finds the **identical plan** to an untraced one.
    So you're watching the actual search, not a replay someone wrote to look like
    one. You may see 2 or 3 imagined states on the same goal — that's genuine
    tie-breaking, explained in Chapter 7.

---

Next: [ask it something →](asking.md)
