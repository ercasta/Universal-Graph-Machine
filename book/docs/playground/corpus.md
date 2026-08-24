# Run a corpus — live

The real engine, in your browser. Type a corpus, list some things to ask
about, and press Run.

This is exactly what `python -m ugm <file> --ask "..."` does, through the
same functions — so anything you can do here you can do at a command line,
and anything printed here was already in the graph before it was printed.

<div class="ugm-playground"
     data-wheel="../wheels/universal_graph_machine-0.4.0-py3-none-any.whl"
     data-mode="corpus">

  <label class="ugm-label" for="ugm-corpus-main">The corpus</label>
  <textarea class="ugm-corpus" id="ugm-corpus-main" rows="12" spellcheck="false">
rule &lt;cancel&gt;     = implies( { +cancelled($f), no disrupted($f) }, { +disrupted($f) } )
rule &lt;weather&gt;    = implies( { +cause($f, storm), no extraordinary($f) }, { +extraordinary($f) } )
rule &lt;care&gt;       = implies( { +disrupted($f), +booked($p, $f), no owed($p, meals) },
                             { +owed($p, meals) } )
rule &lt;compensate&gt; = implies( { +disrupted($f), +booked($p, $f), no extraordinary($f), no owed($p, money) },
                             { +owed($p, money) } )

fact +cancelled(bl204)
fact +cause(bl204, crew)
fact +booked(ana, bl204)
</textarea>

  <label class="ugm-label" for="ugm-asks-main">Ask — one per line</label>
  <textarea class="ugm-asks" id="ugm-asks-main" rows="3" spellcheck="false">owed(ana, money)
owed(ana, meals)
owed(bo, money)</textarea>

  <div class="ugm-controls">
    <button class="ugm-run" type="button">Run</button>
  </div>

  <div class="ugm-quick">
    <span class="ugm-quick-label">Or try:</span>
    <button class="ugm-preset" type="button"
      data-corpus="rule &lt;regen&gt; = implies( { +wounded($x), no poisoned($x), no heals($x) }, { +heals($x) } )

fact +wounded(a)
fact +poisoned(a)
fact +wounded(b)"
      data-asks="heals(a)
heals(b)">absence blocks a rule too</button>
    <button class="ugm-preset" type="button"
      data-corpus="rule &lt;weather&gt; = implies( { +cloudy($d, morning), no likely(rain($d, afternoon)) },
                          { +likely(rain($d, afternoon)) } )
rule &lt;cross&gt;   = implies( { +likely($p), no given(h1, $p) },              { +given(h1, $p) } )
rule &lt;wet&gt;     = implies( { +given($h, rain($d, $t)), no given($h, wet(streets)) },
                          { +given($h, wet(streets)) } )

fact +cloudy(monday, morning)"
      data-asks="likely(rain(monday, afternoon))
given(h1, wet(streets))
wet(streets)">supposing</button>
    <button class="ugm-preset" type="button"
      data-corpus="rule &lt;boil&gt; = implies( { +heat(anna, kettle), +water(kettle), no boiling(kettle) },
                      { +boiling(kettle) } )
rule &lt;use-hob&gt; = implies( { +blocked(heat(anna, kettle)), +has(anna, hob), no doing(heat(anna, kettle)) },
                          { +doing(heat(anna, kettle)) } )

fact +water(kettle)
fact +has(anna, hob)
fact +goal(boiling(kettle))"
      data-asks="boiling(kettle)">a goal, and acting on it</button>
    <button class="ugm-preset" type="button"
      data-corpus="rule &lt;no-harm&gt; = implies( { +producing($r, doing(harm($x))) },
                         { +drop(doing(harm($x))) } )
fact +intercepts(&lt;no-harm&gt;, after)

rule &lt;angry&gt; = implies( { +threatens($x, me), no doing(harm($x)) }, { +doing(harm($x)) } )

fact +threatens(bo, me)"
      data-asks="doing(harm(bo))">a norm that refuses</button>
  </div>

  <div class="ugm-steps"></div>
</div>

!!! note "The first run takes a moment"
    It downloads a Python runtime and installs the engine as a wheel. After that
    it's instant, and it stays loaded while you move between pages.

## What you're looking at

**At load** — notes the loader produced before running anything. The most
useful one is *nothing writes X, and a rule reads it* (Chapter 8): a broken
pairing always leaves some reader with no writer, so a misspelling is caught
whether it landed in the rule or in the fact.

**Ticks, and how it ended.** `quiescent` means applying anything further
would change nothing. `applied` means it hit the limit and had not finished
— which is usually a rule that keeps re-matching its own conclusion (Chapter
7): give a rule a `no` guard on what it's about to assert, or it will fire
again every tick forever.

**What it believes, newest first.** Everything currently anchored — assert
something and it appears; erase it and it's gone, with no scar left behind.

**Believed or not.** Each line you asked about comes back `believed` or `not
believed`. Not believed doesn't mean denied — it means nothing here settled
it, which is a different claim, and Chapter 3 is about why the difference
matters.

## Things worth trying

- Take the `+poisoned(a)` fact out of the first preset and watch `heals(a)`
  flip to `believed` — nothing claims poisoned any more, so the guard is
  satisfied.
- Add `fact dormant(<A>)` about one of two rules and see which conclusions
  disappear — including ones you didn't mean to lose (Chapter 17).
- Delete a rule's own `no ...(...)` guard on its conclusion and watch the run
  end `applied` at the tick limit instead of `quiescent` — that's the rule
  re-matching itself forever.
- In the "a goal, and acting on it" preset, remove `fact +has(anna, hob)` and
  watch `boiling(kettle)` come back `not believed` — the plan had exactly one
  route, and it's gone.

---

[Make it check itself →](selftest.md)
