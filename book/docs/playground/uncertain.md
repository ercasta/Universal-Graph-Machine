# The uncertain case — live

The detective is back — but this time the clues are honest about their doubt.
Ada's alibi is solid; **cy's alibi is shaky** (someone *vaguely* remembers
vouching for them). A neighbour glimpsed the getaway and thinks it was
*probably* cy, *maybe* bo. And the suspects can be ranked by sheer suspicion,
even though nobody ever measured it.

This is the real engine in your browser (first **Run** downloads it once; after
that it's instant). Try these:

- Ask `who is thief` — the answer names its confidence: **cy is thief
  (likely)**, not a flat accusation. Then ask `is cy thief` for the plain
  verdict: **likely**, not *yes* — the conclusion leans on cy's shaky alibi and
  honestly wears that doubt.
- Tick **be cautious** and ask again. Now the machine refuses to lean on an
  absence while the alibi is even *slightly* possible — **likely** becomes
  **no** (assumed). One dial, out in the open.
- Ask `is ada thief` — a solid alibi still clears you outright: **no (assumed)**,
  never a band word. The *(assumed)* is honesty, not doubt — every closed-world
  "no" is a "nothing supports it", and here the machine says so.
- Ask `guess culprit` — the machine collapses the neighbour's glimpse to the
  most possible suspect *and tells you it's guessing*, naming the alternative it
  did **not** rule out.
- Ask `why cy is thief` — the machine shows its work *and its leap*: the
  premises it had, and the line **assumed not: cy is cleared (the
  counter-evidence is only unlikely)**. The jump is on the record.
- Ask `is cy more suspicious than bo` (worked out through ada), then
  `why is cy more suspicious than bo` to see the chain — and
  `is cy more suspicious than dan` for an honest **unknown**: no chain of
  comparisons connects them, and the machine won't invent one.

<div class="ugm-playground" data-mode="world"
     data-wheel="../wheels/universal_graph_machine-0.1.0-py3-none-any.whl">

  <label class="ugm-label" for="ugm-corpus-u">The world — clues, doubts, and rules</label>
  <textarea id="ugm-corpus-u" class="ugm-corpus" spellcheck="false" rows="20">
ada is a suspect
bo is a suspect
cy is a suspect

bo in library
ada is alibied
cy is unlikely alibied

culprit is either bo or more likely cy

suspicious is gradable
ada is more suspicious than bo
cy is more suspicious than ada
dan is more suspicious than bo

?someone is innocent when ?someone in library
?someone is cleared when ?someone is innocent
?someone is cleared when ?someone is alibied
?someone is thief when ?someone is a suspect and ?someone is not cleared
</textarea>

  <div class="ugm-controls">
    <input id="ugm-question-u" class="ugm-question" type="text"
           value="is cy thief" aria-label="Question"
           placeholder="e.g. is cy thief" />
    <button class="ugm-run" type="button">Run</button>
  </div>

  <label class="ugm-openmind">
    <input type="checkbox" class="ugm-cautious" />
    be cautious <span class="ugm-hint">(don't lean on an absence while the
    opposite is even slightly possible — try it on <code>is cy thief</code>)</span>
  </label>

  <div class="ugm-quick">
    <span class="ugm-quick-label">Quick questions:</span>
    <button type="button" class="ugm-ask" data-q="who is thief">who is thief</button>
    <button type="button" class="ugm-ask" data-q="is cy thief">is cy thief</button>
    <button type="button" class="ugm-ask" data-q="is ada thief">is ada thief</button>
    <button type="button" class="ugm-ask" data-q="is cy alibied">is cy alibied</button>
    <button type="button" class="ugm-ask" data-q="guess culprit">guess culprit</button>
    <button type="button" class="ugm-ask" data-q="why cy is thief">why cy is thief</button>
    <button type="button" class="ugm-ask" data-q="is cy more suspicious than bo">is cy more suspicious than bo</button>
    <button type="button" class="ugm-ask" data-q="why is cy more suspicious than bo">why is cy more suspicious than bo</button>
    <button type="button" class="ugm-ask" data-q="is cy more suspicious than dan">is cy more suspicious than dan</button>
  </div>

  <div class="ugm-steps" aria-live="polite">
    <div class="ugm-status">Press Run — the answers here have shades: likely, unlikely, unknown…</div>
  </div>
</div>

!!! question "What can I type?"
    Everything from the [detective case](detective.md), **plus**: hedged clues
    (`cy is unlikely alibied`, `sam is likely a spy`), your own hedge words
    (`probable means 0.7`), correlated alternatives
    (`culprit is either bo or more likely cy`), comparisons
    (`ada is more suspicious than bo`) and comparison questions
    (`is cy more suspicious than dan`, `is fay as suspicious as gil`), and the
    collapse `guess culprit`. Yes/no answers may come back as **certain ·
    very likely · likely · unlikely · very unlikely · no · no (assumed) ·
    unknown**.

!!! tip "Where this is explained"
    Concepts: [Living in an uncertain world](../advanced/10-uncertain-world.md)
    and [More or less](../advanced/11-more-or-less.md). Machinery:
    [Shades of maybe](../deep/17-uncertain-world-internals.md).
