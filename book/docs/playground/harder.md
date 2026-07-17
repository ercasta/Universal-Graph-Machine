# The hard case — think harder, live

Same detective, a harder knot. The reasoning here runs on a **budget** — the
machine only gets so many steps before it has to answer with what it has. When
the trail of evidence is short, a quick glance is plenty. When it's long, a
quick glance **runs out** before the machine reaches the end — and, crucially,
the machine *knows* it ran out, so it says **`unknown`** ("I didn't finish
looking") instead of guessing.

Tick **think it through** to hand it a much bigger budget and press **Run**
again. Watch the honest `unknown` turn into a real answer — and watch it **take
back** a hasty accusation.

Try these:

- Ask `is ada thief` with the box **unticked** — the machine runs out of budget
  partway down her alibi and answers `unknown`. Now **tick the box** and ask
  again: her CCTV alibi checks out four steps deep, and the answer becomes `no`.
- Ask `who is thief` **unticked** — a quick glance can't finish clearing ada, so
  it **over-accuses** her (lists her *and* cy). **Tick the box** and ask again:
  it clears ada and names only `cy`.
- Ask `is cy thief` both ways. Even a *definite* answer needs enough budget to
  finish looking for — and failing to find — a way to clear cy.

!!! tip "About the budget"
    A bigger budget never *changes* a fact — it only lets the machine **finish**.
    That's the whole point: an answer it reaches with more thinking is one it
    would always have reached; the small budget just wasn't enough to get there.
    When it can't finish, it tells you so rather than pretending. (Chapter 20
    explains why this honesty is the heart of the design.)

<div class="ugm-playground" data-mode="harder"
     data-wheel="../wheels/universal_graph_machine-0.1.0-py3-none-any.whl">

  <label class="ugm-label" for="ugm-corpus">The world — clues and rules</label>
  <textarea id="ugm-corpus" class="ugm-corpus" spellcheck="false" rows="16">
ada is a suspect
bo is a suspect
cy is a suspect

ada is filmed
bo is alibied

?p is cleared      when ?p is alibied
?p is alibied      when ?p is corroborated
?p is corroborated when ?p is timestamped
?p is timestamped  when ?p is filmed
?p is thief when ?p is a suspect and ?p is not cleared
</textarea>

  <div class="ugm-controls">
    <input id="ugm-question" class="ugm-question" type="text"
           value="is ada thief" aria-label="Question"
           placeholder="e.g. is ada thief" />
    <button class="ugm-run" type="button">Run</button>
  </div>

  <label class="ugm-openmind">
    <input type="checkbox" class="ugm-think" />
    think it through <span class="ugm-hint">(hand the machine a much bigger
    budget — an <code>unknown</code> it ran out of time on becomes a real answer)</span>
  </label>

  <div class="ugm-quick">
    <span class="ugm-quick-label">Quick questions:</span>
    <button type="button" class="ugm-ask" data-q="is ada thief">is ada thief</button>
    <button type="button" class="ugm-ask" data-q="who is thief">who is thief</button>
    <button type="button" class="ugm-ask" data-q="is cy thief">is cy thief</button>
    <button type="button" class="ugm-ask" data-q="is bo thief">is bo thief</button>
  </div>

  <div class="ugm-steps" aria-live="polite">
    <div class="ugm-status">Press Run and watch the machine reason, step by step…</div>
  </div>
</div>

!!! question "Why does clearing ada take so long?"
    Her alibi is a **chain**: she was `filmed` by a camera, which makes her
    `timestamped`, which makes her `corroborated`, which makes her `alibied`,
    which finally makes her `cleared`. That's four links to follow before the
    machine can rule her out. bo is `alibied` outright — one link — so a quick
    glance clears him. Lengthen ada's chain (add another rule) and even "think
    it through" will eventually need a bigger budget still.

!!! tip "Where this fits"
    This is the same honest-`unknown` you met in
    [the very first detective case](detective.md) — there it came from *missing*
    evidence, here from *unfinished* looking. Both are the machine refusing to
    turn "I don't know yet" into a confident "no." The
    [modes chapter](../deep/17-modes.md) names the budget: eight of the nine ways
    of thinking spend it, and "think harder" just means *more*.
