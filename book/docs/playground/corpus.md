# Run a corpus — live

The real engine, in your browser. Type a corpus, list some things to ask *why*
about, and press Run.

This is exactly what `python -m ugm <file> --why ...` does, through the same two
functions — so anything you can do here you can do at a command line, and
anything printed here was already in the graph before it was printed.

<div class="ugm-playground"
     data-wheel="../wheels/universal_graph_machine-0.4.0-py3-none-any.whl"
     data-mode="corpus">

  <label class="ugm-label" for="ugm-corpus-main">The corpus</label>
  <textarea class="ugm-corpus" id="ugm-corpus-main" rows="12" spellcheck="false">
rule &lt;cancel&gt;     = implies( { +cancelled(?f) }, { +disrupted(?f) } )
rule &lt;crewing&gt;    = implies( { +cause(?f, crew) }, { -extraordinary(?f) } )
rule &lt;weather&gt;    = implies( { +cause(?f, storm) }, { +extraordinary(?f) } )
rule &lt;care&gt;       = implies( { +disrupted(?f), +booked(?p, ?f) },
                             { +owed(?p, meals) } )
rule &lt;compensate&gt; = implies( { +disrupted(?f), +booked(?p, ?f), -extraordinary(?f) },
                             { +owed(?p, money) } )

fact +cancelled(bl204)
fact +cause(bl204, crew)
fact +booked(ana, bl204)
</textarea>

  <label class="ugm-label" for="ugm-asks-main">Ask why — one per line</label>
  <textarea class="ugm-asks" id="ugm-asks-main" rows="3" spellcheck="false">owed(ana, money)
owed(ana, meals)
owed(bo, money)</textarea>

  <div class="ugm-controls">
    <button class="ugm-run" type="button">Run</button>
  </div>

  <div class="ugm-quick">
    <span class="ugm-quick-label">Or try:</span>
    <button class="ugm-preset" type="button"
      data-corpus="rule &lt;regen&gt; = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )

fact +wounded(a)
fact +poisoned(a)
fact +wounded(b)"
      data-asks="heals(a)
heals(b)">silence is not denial</button>
    <button class="ugm-preset" type="button"
      data-corpus="rule &lt;weather&gt; = implies( { +cloudy(?d, morning) }, { +likely(rain(?d, afternoon)) } )
rule &lt;cross&gt;   = implies( { +likely(?p) },              { +given(h1, ?p) } )
rule &lt;wet&gt;     = implies( { +given(?h, rain(?d, ?t)) }, { +given(?h, wet(streets)) } )

fact +cloudy(monday, morning)"
      data-asks="likely(rain(monday, afternoon))
given(h1, wet(streets))
wet(streets)">supposing</button>
    <button class="ugm-preset" type="button"
      data-corpus="rule &lt;boil&gt; = causes( { +heat(anna, kettle), +water(kettle) },
                      { +boiling(kettle) } )
rule &lt;use-hob&gt; = implies( { +blocked(heat(anna, kettle)), +has(anna, hob) },
                          { +doing(heat(anna, kettle)) } )

fact +water(kettle)
fact +has(anna, hob)
fact +goal(boiling(kettle))"
      data-asks="boiling(kettle)">a goal, and acting on it</button>
    <button class="ugm-preset" type="button"
      data-corpus="rule &lt;no-harm&gt; = implies( { +producing(?r, doing(harm(?x))) },
                         { +drop(doing(harm(?x))) } )
fact intercepts(&lt;no-harm&gt;, after)

rule &lt;angry&gt; = implies( { +threatens(?x, me) }, { +doing(harm(?x)) } )

fact +threatens(bo, me)"
      data-asks="doing(harm(bo))">a norm that refuses</button>
  </div>

  <div class="ugm-steps"></div>
</div>

!!! note "The first run takes a moment"
    It downloads a Python runtime and installs the engine as a wheel. After that
    it's instant, and it stays loaded while you move between pages.

## What you're looking at

**At load** — notes the loader produced before running anything. The most useful
one is *nothing writes X, and a rule reads it* (Chapter 8): a broken pairing
always leaves some reader with no writer, so a misspelling is caught whether it
landed in the rule or in the fact.

**Ticks, and how it ended.** `quiescent` means applying anything further would
change nothing. `applied` means it hit the limit and had not finished — which is
usually a rule that keeps re-firing (Chapter 7).

**What became of what was asked for.** Anything you wrote as `+goal(...)`, with
its plans and subgoals, marked `held`, `open` or `BLOCKED`.

**why** — the trail. Each line is a claim still in memory, with its sign, its
locus, where it came from, and what licensed it.

## Things worth trying

- Take the `-poisoned(b)` denial out of a working corpus and watch the rule go
  quiet with nothing saying why.
- Change an `implies` to a `causes` on a rule that keys on `+quiet(?m)` and watch
  it run to the tick limit.
- Add `fact dormant(<A>)` about one of two rules and see which conclusions
  disappear — including ones you didn't mean to lose (Chapter 17).
- Write a rule about your rules: `implies( { +conn(?r, causes) }, { +persists(?r) } )`
  and ask why one of your own rules persists.

---

[Make it check itself →](selftest.md)
