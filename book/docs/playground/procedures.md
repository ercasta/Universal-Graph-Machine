# The procedures case — get things done, live

Teach the machine a routine, run it by name, and watch the steps go by. This
playground *acts*: each step is carried out by a little simulated world that reports
back what happened — exactly the seam a real program would sit on.

Two things make it more than a to-do list:

- **The machine fills gaps.** A step here needs *water*, and no step you wrote
  provides any. Press **Run** and watch it slip in a `fetch_water` step you never
  typed — it planned the missing bit itself and put it in the right place.
- **The machine copes with failure.** Type a step's name into **make this step
  fail** and run again. That step will *finish but achieve nothing* (the mug stays
  cold). The machine notices the effect never appeared, sets that approach aside,
  and reaches for another way to get there.

Try these:

- Press **Run** as-is. The routine is `add_beans then heat`, but `heat` needs water
  — so the machine plans `fetch_water` in between. Order out: `add_beans`,
  **`fetch_water`** *(planned)*, `heat`.
- Click **fail heat**. Now `heat` runs but the coffee never gets hot. The machine
  detects the **discrepancy** and recovers through `microwave`, which makes hot
  coffee another way. Order out: … `heat` *(failed)*, **`microwave`** *(recovered)*.
- Click **fail microwave** *and* set `heat` to fail too (type `heat` in the box,
  then also try failing microwave): with **no** working route left, the machine
  doesn't fake success — it tells you the effect wasn't achieved.
- Edit the routine. Add a step: `to brew : add_beans then heat then serve`, and give
  `serve` an operator (`serve add served`). Run it and watch the new step execute in
  order.

<div class="ugm-playground" data-mode="procedure"
     data-wheel="../wheels/universal_graph_machine-0.1.0-py3-none-any.whl">

  <label class="ugm-label" for="ugm-corpus">The routine — operators, then <code>to … : … then …</code></label>
  <textarea id="ugm-corpus" class="ugm-corpus" spellcheck="false" rows="14">
pre is a relation
add is a relation

add_beans add grounds
fetch_water add water
heat pre grounds
heat pre water
heat add hot_coffee
microwave pre grounds
microwave add hot_coffee

to brew : add_beans then heat
</textarea>

  <div class="ugm-controls">
    <input id="ugm-question" class="ugm-question" type="text"
           value="run brew" aria-label="Command"
           placeholder="e.g. run brew" />
    <button class="ugm-run" type="button">Run</button>
  </div>

  <label class="ugm-openmind">
    make this step fail:
    <input type="text" class="ugm-fail" value="" aria-label="Step to fail"
           placeholder="(none)" style="width:9em" />
    <span class="ugm-hint">it runs but achieves nothing — watch the machine recover</span>
  </label>

  <div class="ugm-quick">
    <span class="ugm-quick-label">Quick runs:</span>
    <button type="button" class="ugm-ask" data-q="run brew" data-fail="">run brew (gap-fill)</button>
    <button type="button" class="ugm-ask" data-q="run brew" data-fail="heat">fail heat</button>
    <button type="button" class="ugm-ask" data-q="run brew" data-fail="microwave">fail microwave</button>
  </div>

  <div class="ugm-steps" aria-live="polite">
    <div class="ugm-status">Press Run and watch the machine act, step by step…</div>
  </div>
</div>

!!! question "Where did `fetch_water` come from?"
    You wrote `to brew : add_beans then heat` — two steps. But `heat` declares it
    **needs** water (`heat pre water`), and nothing you wrote produces water. The
    machine treats that gap as a tiny planning problem: it finds an operator that
    *adds* water (`fetch_water`), commits to it, and — because a producer must come
    before its consumer — runs it *before* `heat`. Your pre-made plan and the
    machine's synthesized step go through **one** execution gate; from the outside
    you can't tell which was yours.

!!! tip "Failure is data, not a crash"
    When a step finishes without its effect, the machine doesn't throw an error and
    it doesn't pretend it worked. It records a plain **fact** — *this didn't take* —
    that ordinary rules react to. The built-in reaction is the sensible one: don't
    retry what just failed, find another route. And if there isn't one, it says so.
    That's the same honesty as the [`unknown`](../intermediate/05-no-and-unknown.md)
    answer — here pointed at *doing* instead of *knowing*.

!!! note "Why this isn't a new kind of thinking"
    Sequencing, gap-filling, noticing failure, recovering — none of it is a new
    engine feature. It's the [nine ways of thinking](../deep/18-modes.md) *composed*:
    step through a list, make a call, check the result, react with more rules. The
    whole routine lives in the knowledge base, not in the machine.
