# The detective case — live

This is the real Universal Graph Machine, running **in your browser**. Nothing
is sent to a server — the whole engine is loaded onto your device the first time
you press **Run** (that first load takes a few seconds; after that it's
instant).

Edit the clues and rules, type a question, and press **Run** — then **watch the
machine reason one step at a time**: the goal it sets, the **questions it asks
itself** along the way (like *"is cy cleared?"*) and whether it finds evidence,
and finally its answer. Try these:

- Ask `who is thief` — then **delete the line `ada is alibied`** and ask again.
- Ask `who is nervous` to have the machine sweep the world for a plain quality.
- Ask `why cy is thief` to see the machine's own reasoning trail.
- Ask `is zz thief` — then tick **keep an open mind** and ask the *same*
  question again. Watch `no` become `unknown`. (It also flips `is ada thief`.)

!!! tip "About *keep an open mind*"
    This switch only changes answers the machine **can't prove** — a defeasible
    `no` becomes `unknown`. It has **no effect** on questions it *can* prove, like
    `who is thief` or `is cy thief`: proof doesn't care about your attitude toward
    missing evidence. So try it on `is ada thief` or `is zz thief` to see it work.
    (Chapter 5 explains why.)

<div class="ugm-playground"
     data-wheel="../wheels/universal_graph_machine-0.1.0-py3-none-any.whl">

  <label class="ugm-label" for="ugm-corpus">The world — clues and rules</label>
  <textarea id="ugm-corpus" class="ugm-corpus" spellcheck="false" rows="13">
ada is a suspect
bo is a suspect
cy is a suspect

ada is nervous
bo in library
ada is alibied

?someone is innocent when ?someone in library
?someone is cleared when ?someone is innocent
?someone is cleared when ?someone is alibied
?someone is thief when ?someone is a suspect and ?someone is not cleared
</textarea>

  <div class="ugm-controls">
    <input id="ugm-question" class="ugm-question" type="text"
           value="who is thief" aria-label="Question"
           placeholder="e.g. who is thief" />
    <button class="ugm-run" type="button">Run</button>
  </div>

  <label class="ugm-openmind">
    <input type="checkbox" class="ugm-open" />
    keep an open mind <span class="ugm-hint">(an unprovable answer becomes
    "unknown" instead of "no" — try it on <code>is ada thief</code>)</span>
  </label>

  <div class="ugm-quick">
    <span class="ugm-quick-label">Quick questions:</span>
    <button type="button" class="ugm-ask" data-q="who is thief">who is thief</button>
    <button type="button" class="ugm-ask" data-q="who is nervous">who is nervous</button>
    <button type="button" class="ugm-ask" data-q="is cy thief">is cy thief</button>
    <button type="button" class="ugm-ask" data-q="is ada thief">is ada thief</button>
    <button type="button" class="ugm-ask" data-q="why cy is thief">why cy is thief</button>
    <button type="button" class="ugm-ask" data-q="is zz thief">is zz thief</button>
  </div>

  <div class="ugm-steps" aria-live="polite">
    <div class="ugm-status">Press Run and watch the machine reason, step by step…</div>
  </div>
</div>

!!! question "What can I type?"
    **Clues** look like `bo in library`, `ada is a suspect`, or `ada is
    alibied`. **Rules** use the word *when*: `someone is X when they are Y`.
    **Questions** are things like `who is thief`, `is cy thief`, or `why cy is
    thief`. If you type something the machine doesn't understand, it will say so
    rather than guess — that's the point.
