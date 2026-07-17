/*
 * UGM live playground — "watch it think" step view.
 *
 * Loads Pyodide (on demand, once), installs the pure-Python `ugm` wheel with
 * micropip, and runs the real engine in the browser. No server.
 *
 * The engine streams real reasoning events (`ingest(..., trace=True)`):
 *   - `subgoal` : a question the machine asked ITSELF (a demand-driven NAF
 *                 check, e.g. "is cy cleared?") and whether it found anything;
 *   - `derive`  : a fact it worked out and the rule it used;
 *   - `answer`  : the verdict.
 * We animate that stream so you literally watch it reason. NAF checks tell the
 * cleanest story, so we lead with them, then show the facts it worked out
 * (each naming the rule that produced it).
 *
 * Document-level event delegation keeps this working under Material's
 * `navigation.instant` (SPA-style) page swaps.
 */
(function () {
  "use strict";

  var PYODIDE_VERSION = "0.26.4";
  var PYODIDE_BASE =
    "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_VERSION + "/full/";
  var STEP_DELAY_MS = 750; // pause between reasoning steps

  // The shipped planner banks the procedures playground runs on (corpus/procedure.cnl +
  // planning.cnl + planning_execution.cnl, comments stripped — the wheel doesn't bundle the .cnl
  // files). Kept in sync with those files; content-blind (no domain word appears here).
  var PROC_BANKS = [
    "?s chosen <yes> when <run> proc ?p and ?p step ?s",
    "?a before ?b when <run> proc ?p and ?a step_before ?b",
    "<need> for ?p when ?o chosen <yes> and ?o pre ?p and not <now> true ?p",
    "?o discrepancy ?e when ?o done <yes> and ?o add ?e and not <now> true ?e",
    "?o excluded <yes> when ?o discrepancy ?e",
    "?alt chosen <yes> when ?o discrepancy ?e and ?alt add ?e and not ?alt done <yes> and not ?alt excluded <yes>",
    "drop ?o discrepancy ?e when ?o discrepancy ?e and <now> true ?e",
    "<need> for ?c when <goal> want ?c",
    "?o candidate ?c when <need> for ?c and ?o add ?c and not ?o excluded <yes>",
    "<need> for ?p when ?o candidate ?c and ?o pre ?p",
    "?c reachable <yes> when <now> true ?c",
    "?o blocked_by ?p when ?o candidate ?g and ?o pre ?p and not ?p reachable <yes>",
    "drop ?o blocked_by ?p when ?o blocked_by ?p and ?p reachable <yes>",
    "?o viable <yes> when ?o candidate ?g and not ?o blocked_by ?anyp",
    "?c reachable <yes> when ?o viable <yes> and ?o add ?c",
    "?o cost_settled <yes> when ?o price_known <yes>",
    "?o cost_settled <yes> when ?o viable <yes> and not ?o needs_price <yes>",
    "<call>? tool rank and <call>? arg ?o when ?o cost_settled <yes> and not ?o ranked <yes>",
    "?o dominated <yes> when ?o viable <yes> and ?o cost_settled <yes> and ?o add ?c and ?x viable <yes> and ?x cost_settled <yes> and ?x add ?c and ?x cheaper_than ?o",
    "?o best <yes> when ?o viable <yes> and ?o cost_settled <yes> and not ?o dominated <yes>",
    "?o chosen <yes> when <need> for ?c and ?o best <yes> and ?o add ?c and not ?x chosen <yes> and not ?x add ?c",
    "?o1 before ?o2 when ?o1 chosen <yes> and ?o2 chosen <yes> and ?o1 add ?c and ?o2 pre ?c",
    "?o unmet ?p when ?o chosen <yes> and ?o pre ?p and not <now> true ?p",
    "drop ?o unmet ?p when ?o unmet ?p and <now> true ?p",
    "?o waits_for ?b when ?o chosen <yes> and ?b before ?o and not ?b done <yes>",
    "drop ?o waits_for ?b when ?o waits_for ?b and ?b done <yes>",
    "<exec> ready ?o when ?o chosen <yes> and not ?o unmet ?anyp and not ?o waits_for ?anyb and not ?o done <yes>",
    "<call>? tool act and <call>? arg ?o when <exec> ready ?o",
  ].join("\n");

  // Defined once after install. Returns a JSON string (avoids proxy fiddliness).
  var BOOTSTRAP = [
    "import ugm as _h, json as _json",
    "from ugm import FirmwarePolicy as _FP, DEFAULT_POLICY as _DP",
    "from ugm.dispatch import call_arg as _call_arg",
    "",
    "def _ugm_run(corpus, question, open_mind, max_rounds=1000):",
    "    # `max_rounds` is the reasoning BUDGET (\"think harder\" = a bigger budget, ugm.intake §14 fuel):",
    "    # a chain deeper than the budget leaves the closure short of fixpoint, and that surfaces as an",
    "    # honest `unknown` rather than a confident guess. Default 1000 = plenty (the detective page).",
    "    try:",
    "        kb, rules = _h.load_corpus(corpus)",
    "    except Exception as e:",
    "        return _json.dumps({'error': 'I could not read the world: ' + str(e)})",
    "    pol = _FP(negation_default='open') if open_mind else _DP",
    "    checks, derives = [], []",
    "    def cap(ev):",
    "        if ev.kind == 'subgoal':",
    "            d = ev.data",
    "            checks.append({'subj': d.get('subj'), 'pred': d.get('pred'),",
    "                           'obj': d.get('obj'), 'found': bool(d.get('found'))})",
    "        elif ev.kind == 'derive':",
    "            derives.append({'rule': ev.data.get('rule',''), 'fact': ev.data.get('fact','')})",
    "    try:",
    "        out = _h.ingest(kb, rules, question, on_event=cap, trace=True, policy=pol,",
    "                        max_rounds=int(max_rounds))",
    "    except Exception as e:",
    "        return _json.dumps({'error': 'I could not make sense of that question: ' + str(e)})",
    "    return _json.dumps({'error': None, 'kind': out.kind, 'question': question,",
    "                        'open_mind': bool(open_mind), 'checks': checks, 'derives': derives,",
    "                        'answer': list(out.answer) if out.answer else []})",
    "",
    "def _ugm_run_world(corpus, question, cautious):",
    "    # The COMPOSITE surface (uncertain + comparative + guess), answered under the BANDED",
    "    # firmware stance — verdicts may be 'likely'/'unlikely'/…; 'be cautious' lowers theta.",
    "    # A STANCE META-LINE ('be cautious' / 'be decisive') is recognized by the engine itself",
    "    # (policy.recognize_stance — a form + the declared STANCES table) and answered as a",
    "    # 'stance' result; the page then sets the checkbox to match, so the dial IS the CNL.",
    "    from ugm.policy import recognize_stance, STANCES",
    "    stance = recognize_stance(question)",
    "    if stance is not None:",
    "        word = next((w for w, p in STANCES.items() if p == stance), 'cautious')",
    "        note = ('I will not lean on an absence while the opposite is even slightly possible.'",
    "                if word == 'cautious' else",
    "                'I will make the jump when the counter-evidence is unlikely — and say so.')",
    "        return _json.dumps({'error': None, 'kind': 'stance', 'stance': word,",
    "                            'question': question, 'checks': [], 'derives': [],",
    "                            'answer': ['stance set: ' + word + ' — ' + note]})",
    "    from ugm.cnl.world import load_world, ask_world",
    "    from ugm.cnl.surface import render_relation as _rr, _band_suffix as _bs",
    "    from ugm.intake import _j_nodes",
    "    from ugm.possibility import band_word as _bw",
    "    from ugm import provenance as _prov",
    "    try:",
    "        kb, rules = load_world(corpus)",
    "    except Exception as e:",
    "        return _json.dumps({'error': 'I could not read the world: ' + str(e)})",
    "    pol = _FP(uncertainty='banded', theta=0.2 if cautious else 0.5)",
    "    subgoals, before = [], _j_nodes(kb)",
    "    try:",
    "        ans = ask_world(kb, rules, question, policy=pol, provenance=True,",
    "                        on_subgoal=lambda rec: subgoals.append(dict(rec)))",
    "    except Exception as e:",
    "        return _json.dumps({'error': 'I could not make sense of that question: ' + str(e)})",
    "    # Same collapse as ingest's trace stream: only the NAF checks (resolve phase, depth>=1;",
    "    # the depth-0 record is the goal itself — a WILDCARD subject for wh-questions, which",
    "    # would render as 'null is thief'), ONE entry per distinct check in first-seen order,",
    "    # `found` monotone across re-entries (the chain may resolve the same check twice).",
    "    seen, checks = {}, []",
    "    for rec in subgoals:",
    "        if rec.get('phase') != 'resolve' or rec.get('depth', 0) < 1:",
    "            continue",
    "        key = (rec.get('pred'), rec.get('subj'), rec.get('obj'))",
    "        b = rec.get('band')",
    "        w = _bw(b) if (b is not None and b < 1.0) else None",
    "        if key not in seen:",
    "            seen[key] = {'subj': rec.get('subj'), 'pred': rec.get('pred'),",
    "                         'obj': rec.get('obj'), 'found': bool(rec.get('found')), 'word': w}",
    "            checks.append(seen[key])",
    "        elif rec.get('found') and not seen[key]['found']:",
    "            seen[key]['found'], seen[key]['word'] = True, w",
    "    # What it worked out, each fact wearing its OWN band and naming its rule: the",
    "    # provenance J-nodes this question added, in creation (= derivation) order.",
    "    derives = []",
    "    for j in sorted(_j_nodes(kb) - before, key=lambda n: (len(n), n)):",
    "        for fact in _prov.proven_of(kb, j):",
    "            r = _rr(kb, fact)",
    "            if r is not None:",
    "                derives.append({'rule': _prov.rule_of_j(kb, j), 'fact': r + _bs(kb, fact)})",
    "    return _json.dumps({'error': None, 'kind': 'answer', 'question': question,",
    "                        'checks': checks, 'derives': derives, 'answer': list(ans)})",
    "",
    // The PROCEDURES surface: author a routine + operators, run it, execute steps via a sim tool.
    "def _ugm_run_procedure(corpus, command, fail):",
    "    # Author operators + the routine from the corpus, then RUN it, executing each step through a",
    "    # simulated world (`act` tool): materialize its declared effects, unless it is the `fail` step —",
    "    # which finishes but achieves nothing, so the machine detects a discrepancy and replans. The",
    "    # planner banks (procedure/planning/execution) are inlined as _PROC_BANKS.",
    "    try:",
    "        kb = _h.AttrGraph()",
    "        banks = _h.load_machine_rules(_PROC_BANKS)",
    "        for line in corpus.splitlines():",
    "            s = line.strip()",
    "            if s:",
    "                _h.ingest(kb, [], s)",
    "    except Exception as e:",
    "        return _json.dumps({'error': 'I could not read the routine: ' + str(e)})",
    "    order = []",
    "    def _ens(g, n):",
    "        f = g.nodes_named(n)",
    "        return f[0] if f else g.add_node(n)",
    "    def _act(g, cid):",
    "        o = _call_arg(g, cid, 'arg')",
    "        if o is None or any(g.has_key(r, 'done') for r, _ in g.relations_from(o)):",
    "            return set()",
    "        nm = g.name(o); order.append(nm); touched = set()",
    "        now, yes = _ens(g, '<now>'), _ens(g, '<yes>')",
    "        if nm != fail:",
    "            for r, e in list(g.relations_from(o)):",
    "                if g.has_key(r, 'add'): touched.add(g.add_relation(now, 'true', e))",
    "        touched.add(g.add_relation(o, 'done', yes)); return touched",
    "    def _rank(g, cid):",
    "        o = _call_arg(g, cid, 'arg')",
    "        return {g.add_relation(o, 'ranked', _ens(g, '<yes>'))} if o else set()",
    "    try:",
    "        _h.ingest(kb, banks, command, tools={'act': _act, 'rank': _rank})",
    "    except Exception as e:",
    "        return _json.dumps({'error': 'I could not run that: ' + str(e)})",
    "    authored = {kb.name(o) for p in kb.nodes() for r, o in kb.relations_from(p) if kb.predicate(r) == 'step'}",
    "    def _marked(nm, key):",
    "        n = kb.nodes_named(nm)",
    "        return bool(n) and any(kb.predicate(r) == key for r, _ in kb.relations_from(n[0]))",
    "    def _adds(nm):",
    "        n = kb.nodes_named(nm)",
    "        return {kb.name(o) for r, o in kb.relations_from(n[0]) if kb.predicate(r) == 'add'} if n else set()",
    "    failed_effects = set()",
    "    for nm in order:",
    "        if _marked(nm, 'excluded') or _marked(nm, 'discrepancy'): failed_effects |= _adds(nm)",
    "    steps = []",
    "    for nm in order:",
    "        if _marked(nm, 'excluded') or _marked(nm, 'discrepancy'):",
    "            steps.append({'op': nm, 'status': 'failed', 'effect': ', '.join(sorted(_adds(nm)))})",
    "        elif nm in authored:",
    "            steps.append({'op': nm, 'status': 'did'})",
    "        elif _adds(nm) & failed_effects:",
    "            steps.append({'op': nm, 'status': 'recovered', 'effect': ', '.join(sorted(_adds(nm)))})",
    "        else:",
    "            steps.append({'op': nm, 'status': 'planned', 'effect': ', '.join(sorted(_adds(nm)))})",
    "    now = kb.nodes_named('<now>')",
    "    achieved = sorted(set(kb.name(o) for r, o in kb.relations_from(now[0]) if kb.has_key(r, 'true'))) if now else []",
    "    return _json.dumps({'error': None, 'kind': 'procedure', 'command': command, 'steps': steps, 'achieved': achieved})",
    "",
  ].join("\n") + "\n_PROC_BANKS = " + JSON.stringify(PROC_BANKS);

  var enginePromise = null; // shared across all playgrounds on the page
  var runTokens = new WeakMap(); // per-container animation cancellation

  function sleep(ms) {
    return new Promise(function (r) {
      setTimeout(r, ms);
    });
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () {
        reject(new Error("Could not load " + src));
      };
      document.head.appendChild(s);
    });
  }

  function wheelUrl(container) {
    return new URL(container.getAttribute("data-wheel"), document.baseURI).href;
  }

  function getEngine(container, onProgress) {
    if (enginePromise) return enginePromise;
    enginePromise = (async function () {
      onProgress("Waking the machine (downloading the engine, one-time)…");
      await loadScript(PYODIDE_BASE + "pyodide.js");
      var pyodide = await loadPyodide({ indexURL: PYODIDE_BASE });
      onProgress("Loading the reasoning engine…");
      await pyodide.loadPackage("micropip");
      var micropip = pyodide.pyimport("micropip");
      await micropip.install(wheelUrl(container));
      pyodide.runPython(BOOTSTRAP);
      return pyodide;
    })().catch(function (err) {
      enginePromise = null; // allow retry on a later click
      throw err;
    });
    return enginePromise;
  }

  // --- rendering ----------------------------------------------------------

  function stepsEl(container) {
    return container.querySelector(".ugm-steps");
  }

  function ruleLabel(rule) {
    var parts = String(rule).split("."); // "rule.?someone.is.thief" -> "thief"
    return parts[parts.length - 1] || rule;
  }

  // The bound subject of a question, if any ("is cy thief" -> "cy",
  // "why cy is thief" -> "cy"); null for wh-questions ("who is thief").
  function boundSubject(question) {
    var m = /^\s*(?:is|does|why)\s+([a-z0-9_]+)\b/i.exec(question);
    if (!m) return null;
    if (/^\s*why\b/i.test(question) && m[1] === "is") return null;
    return m[1].toLowerCase();
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function addCard(host, kind, build) {
    var card = el("div", "ugm-step ugm-step-" + kind);
    build(card);
    host.appendChild(card);
    requestAnimationFrame(function () {
      card.classList.add("ugm-step-in");
    });
    return card;
  }

  function renderGoal(host, question) {
    addCard(host, "goal", function (card) {
      card.appendChild(el("span", "ugm-step-icon", "🎯"));
      var body = el("div", "ugm-step-body");
      body.appendChild(el("div", "ugm-step-title", "The question"));
      body.appendChild(el("div", "ugm-step-fact", question));
      card.appendChild(body);
    });
  }

  function renderCheck(host, check) {
    var kind = check.found ? "check-yes" : "check-no";
    addCard(host, kind, function (card) {
      card.appendChild(el("span", "ugm-step-icon", "🔍"));
      var body = el("div", "ugm-step-body");
      body.appendChild(el("div", "ugm-step-title", "It asked itself"));
      body.appendChild(
        el("div", "ugm-step-fact",
          (check.subj || "someone") + " " + check.pred + " " + (check.obj || "anything") + " ?")
      );
      body.appendChild(
        el(
          "div",
          "ugm-step-rule",
          check.found
            ? check.word
              ? "→ found something — but it's only " + check.word
              : "→ yes — found evidence"
            : "→ found no evidence"
        )
      );
      card.appendChild(body);
    });
  }

  function renderDerive(host, step) {
    addCard(host, "derive", function (card) {
      card.appendChild(el("span", "ugm-step-icon", "⚙️"));
      var body = el("div", "ugm-step-body");
      body.appendChild(el("div", "ugm-step-title", "Worked out"));
      body.appendChild(el("div", "ugm-step-fact", step.fact));
      body.appendChild(
        el("div", "ugm-step-rule", "using the “" + ruleLabel(step.rule) + "” rule")
      );
      card.appendChild(body);
    });
  }

  // yes/no/unknown plus the GRADED verdicts of the uncertain world (band words),
  // and the kind-wearing CWA default of the banded stance.
  var VERDICTS = [
    "yes", "no", "unknown", "certain",
    "very likely", "likely", "unlikely", "very unlikely", "no (assumed)",
  ];

  function renderAnswer(host, answer) {
    var single = answer.length === 1 ? answer[0].trim() : null;
    var verdict = single && VERDICTS.indexOf(single) >= 0 ? single : null;
    addCard(host, "answer", function (card) {
      card.appendChild(
        el("span", "ugm-step-icon", verdict === "unknown" ? "❔" : "✅")
      );
      var body = el("div", "ugm-step-body");
      body.appendChild(el("div", "ugm-step-title", "Answer"));
      if (verdict) {
        var cls = verdict.replace(/[^a-z]+/g, "-").replace(/^-+|-+$/g, ""); // "no (assumed)" -> "no-assumed"
        body.appendChild(el("div", "ugm-verdict ugm-verdict-" + cls, verdict));
      } else {
        body.appendChild(el("pre", "ugm-answer-text", answer.join("\n")));
      }
      card.appendChild(body);
    });
  }

  function renderNote(host, text) {
    addCard(host, "note", function (card) {
      card.appendChild(el("span", "ugm-step-icon", "💡"));
      var body = el("div", "ugm-step-body");
      body.appendChild(el("div", "ugm-step-fact", text));
      card.appendChild(body);
    });
  }

  // --- procedures: what the machine DID, step by step ---------------------

  function renderCommand(host, command) {
    addCard(host, "goal", function (card) {
      card.appendChild(el("span", "ugm-step-icon", "▶️"));
      var body = el("div", "ugm-step-body");
      body.appendChild(el("div", "ugm-step-title", "The routine"));
      body.appendChild(el("div", "ugm-step-fact", command));
      card.appendChild(body);
    });
  }

  // status -> {css kind, icon, title, note(step)}. `did` = a step you wrote; `planned` = one the
  // machine slipped in to fill a gap; `failed` = it ran but the effect never appeared; `recovered`
  // = an alternative it reached for after a failure.
  var PROC_STEP = {
    did: { kind: "derive", icon: "✔️", title: "Did the step",
      note: function () { return "a step you wrote"; } },
    planned: { kind: "check-yes", icon: "🧩", title: "Planned a step you didn't write",
      note: function (s) { return "to get " + (s.effect || "what came next") + " — the gap filled itself"; } },
    failed: { kind: "check-no", icon: "⚠️", title: "Ran — but nothing happened",
      note: function (s) { return "expected " + (s.effect || "an effect") + ", the world didn't deliver"; } },
    recovered: { kind: "check-yes", icon: "♻️", title: "Tried another way",
      note: function (s) { return "reached for this to get " + (s.effect || "the effect") + " instead"; } },
  };

  function renderProcStep(host, step) {
    var spec = PROC_STEP[step.status] || PROC_STEP.did;
    addCard(host, spec.kind, function (card) {
      card.appendChild(el("span", "ugm-step-icon", spec.icon));
      var body = el("div", "ugm-step-body");
      body.appendChild(el("div", "ugm-step-title", spec.title));
      body.appendChild(el("div", "ugm-step-fact", step.op));
      body.appendChild(el("div", "ugm-step-rule", "→ " + spec.note(step)));
      card.appendChild(body);
    });
  }

  function renderAchieved(host, achieved) {
    var done = achieved && achieved.length;
    addCard(host, done ? "answer" : "check-no", function (card) {
      card.appendChild(el("span", "ugm-step-icon", done ? "✅" : "❔"));
      var body = el("div", "ugm-step-body");
      body.appendChild(el("div", "ugm-step-title", "In the end"));
      body.appendChild(
        el("div", "ugm-step-fact",
          done ? "the world now shows: " + achieved.join(", ")
               : "nothing was achieved — and the machine says so, rather than pretend")
      );
      card.appendChild(body);
    });
  }

  async function animate(container, result, token) {
    var host = stepsEl(container);
    host.innerHTML = "";

    if (result.error) {
      renderNote(host, result.error);
      return;
    }
    if (result.kind === "stance") {
      // The typed dial: "be cautious" / "be decisive" sets the SAME checkbox the page exposes —
      // the stance line and the switch are one control, so the next Run reasons under it.
      var box = container.querySelector(".ugm-cautious");
      if (box) box.checked = result.stance === "cautious";
      renderNote(host, (result.answer && result.answer[0]) || "Stance set.");
      return;
    }
    if (result.kind === "procedure") {
      renderCommand(host, result.command);
      var steps = result.steps || [];
      for (var s = 0; s < steps.length; s++) {
        await sleep(STEP_DELAY_MS);
        if (runTokens.get(container) !== token) return;
        renderProcStep(host, steps[s]);
      }
      await sleep(STEP_DELAY_MS);
      if (runTokens.get(container) !== token) return;
      renderAchieved(host, result.achieved);
      return;
    }
    if (result.kind !== "answer") {
      renderNote(
        host,
        "That looks like a " +
          result.kind +
          ", not a question. Try something like: who is thief"
      );
      return;
    }

    renderGoal(host, result.question);

    // Lead with the NAF checks (the machine's own questions). For a question
    // about a specific suspect, show only the checks about THAT suspect.
    var subj = boundSubject(result.question);
    var checks = result.checks || [];
    if (subj) checks = checks.filter(function (c) { return c.subj === subj; });

    for (var i = 0; i < checks.length; i++) {
      await sleep(STEP_DELAY_MS);
      if (runTokens.get(container) !== token) return;
      renderCheck(host, checks[i]);
    }

    // Then the facts it worked out — each names the rule that produced it.
    var derives = result.derives || [];
    for (var j = 0; j < derives.length; j++) {
      await sleep(STEP_DELAY_MS);
      if (runTokens.get(container) !== token) return;
      renderDerive(host, derives[j]);
    }

    await sleep(STEP_DELAY_MS);
    if (runTokens.get(container) !== token) return;
    renderAnswer(host, result.answer || []);
  }

  // --- run ----------------------------------------------------------------

  async function run(container) {
    var host = stepsEl(container);
    var question = container.querySelector(".ugm-question").value.trim();
    var corpus = container.querySelector(".ugm-corpus").value;
    var mode = container.getAttribute("data-mode");
    var world = mode === "world"; // the uncertain-case page
    var harder = mode === "harder"; // the think-harder page (a reasoning-budget dial)
    var procedure = mode === "procedure"; // the procedures page (run a routine, fail a step)
    var openBox = container.querySelector(".ugm-open");
    var openMind = openBox && openBox.checked;
    var cautiousBox = container.querySelector(".ugm-cautious");
    var cautious = cautiousBox && cautiousBox.checked;
    // "think it through" = a bigger budget; unchecked = a quick glance that may run out of budget.
    var thinkBox = container.querySelector(".ugm-think");
    var budget = thinkBox && thinkBox.checked ? 1000 : 3;

    if (!question) {
      host.innerHTML = "";
      renderNote(host, procedure
        ? "Type a command first — e.g. run brew"
        : "Type a question first — e.g. who is thief");
      return;
    }

    var token = {};
    runTokens.set(container, token); // cancels any in-flight animation

    var buttons = container.querySelectorAll("button");
    buttons.forEach(function (b) {
      b.disabled = true;
    });
    host.innerHTML = "";
    var status = el("div", "ugm-status", "Thinking…");
    host.appendChild(status);

    try {
      var pyodide = await getEngine(container, function (msg) {
        status.textContent = msg;
      });
      if (runTokens.get(container) !== token) return;
      var fn = pyodide.globals.get(
        world ? "_ugm_run_world" : procedure ? "_ugm_run_procedure" : "_ugm_run"
      );
      var failInput = container.querySelector(".ugm-fail");
      var failStep = failInput ? failInput.value.trim() : "";
      var json = world
        ? fn(corpus, question, !!cautious)
        : procedure
          ? fn(corpus, question, failStep) // question field holds the command (`run brew`)
          : harder
            ? fn(corpus, question, false, budget) // the think-harder dial: budget from the checkbox
            : fn(corpus, question, !!openMind);
      fn.destroy();
      var result = JSON.parse(json);
      await animate(container, result, token);
    } catch (err) {
      host.innerHTML = "";
      renderNote(
        host,
        "Something went wrong starting the machine: " +
          (err && err.message ? err.message : err) +
          " — check your connection and press Run to try again."
      );
    } finally {
      buttons.forEach(function (b) {
        b.disabled = false;
      });
    }
  }

  // --- event delegation ---------------------------------------------------

  document.addEventListener("click", function (e) {
    var target = e.target;
    if (!(target instanceof Element)) return;

    var runBtn = target.closest(".ugm-run");
    if (runBtn) {
      var c = runBtn.closest(".ugm-playground");
      if (c) run(c);
      return;
    }

    var askBtn = target.closest(".ugm-ask");
    if (askBtn) {
      var c2 = askBtn.closest(".ugm-playground");
      if (c2) {
        var q = c2.querySelector(".ugm-question");
        q.value = askBtn.getAttribute("data-q") || q.value;
        // procedures: a quick button may also set which step fails (data-fail; "" clears it)
        var failField = c2.querySelector(".ugm-fail");
        if (failField && askBtn.hasAttribute("data-fail")) {
          failField.value = askBtn.getAttribute("data-fail");
        }
        run(c2);
      }
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    var target = e.target;
    if (!(target instanceof Element)) return;
    if (!target.classList.contains("ugm-question")) return;
    e.preventDefault();
    var c = target.closest(".ugm-playground");
    if (c) run(c);
  });
})();
