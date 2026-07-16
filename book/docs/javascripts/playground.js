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

  // Defined once after install. Returns a JSON string (avoids proxy fiddliness).
  var BOOTSTRAP = [
    "import ugm as _h, json as _json",
    "from ugm import FirmwarePolicy as _FP, DEFAULT_POLICY as _DP",
    "",
    "def _ugm_run(corpus, question, open_mind):",
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
    "        out = _h.ingest(kb, rules, question, on_event=cap, trace=True, policy=pol)",
    "    except Exception as e:",
    "        return _json.dumps({'error': 'I could not make sense of that question: ' + str(e)})",
    "    return _json.dumps({'error': None, 'kind': out.kind, 'question': question,",
    "                        'open_mind': bool(open_mind), 'checks': checks, 'derives': derives,",
    "                        'answer': list(out.answer) if out.answer else []})",
    "",
    "def _ugm_run_world(corpus, question, cautious):",
    "    # The COMPOSITE surface (uncertain + comparative + guess), answered under the BANDED",
    "    # firmware stance — verdicts may be 'likely'/'unlikely'/…; 'be cautious' lowers theta.",
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
  ].join("\n");

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

  async function animate(container, result, token) {
    var host = stepsEl(container);
    host.innerHTML = "";

    if (result.error) {
      renderNote(host, result.error);
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
    var world = container.getAttribute("data-mode") === "world"; // the uncertain-case page
    var openBox = container.querySelector(".ugm-open");
    var openMind = openBox && openBox.checked;
    var cautiousBox = container.querySelector(".ugm-cautious");
    var cautious = cautiousBox && cautiousBox.checked;

    if (!question) {
      host.innerHTML = "";
      renderNote(host, "Type a question first — e.g. who is thief");
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
      var fn = pyodide.globals.get(world ? "_ugm_run_world" : "_ugm_run");
      var json = fn(corpus, question, world ? !!cautious : !!openMind);
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
