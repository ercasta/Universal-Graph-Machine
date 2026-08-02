/*
 * The live playground — watch the machine plan, in your browser.
 *
 * Loads Pyodide on demand, installs the pure-Python `ugm` wheel with
 * micropip, and runs the real engine. No server.
 *
 * ⚠ The engine streams REAL search events through `driver.pursue(trace=...)`:
 *
 *   goal      — the goal was taken on, and which constraints are open
 *   refuse    — an action was pruned by a `never` / `at most` constraint. This is
 *               the interesting one: it means the machine did NOT imagine it, and
 *               that is invisible in any after-the-fact record.
 *   consider  — a move was ranked (band 0-4: 4 = "writes exactly this constraint")
 *   imagine   — a move was actually tried on the workbench; `open` is what's left
 *   found     — a plan, with its steps
 *   exhausted — no plan, and why
 *
 * The trace hook is an OBSERVER: the engine's own selftest asserts that a traced
 * search finds the identical plan to an untraced one. So this animation is the
 * real run, not a reconstruction of one.
 *
 * Document-level event delegation keeps this working under Material's
 * `navigation.instant` (SPA-style) page swaps.
 */
(function () {
  "use strict";

  var PYODIDE_VERSION = "0.26.4";
  var PYODIDE_BASE =
    "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_VERSION + "/full/";
  var STEP_DELAY_MS = 420;

  // ── The Python side, defined once after install ────────────────────────────
  //
  // Returns a JSON string rather than a proxy object — proxies across the JS/Py
  // boundary are fiddly, and this is a one-way report.
  var BOOTSTRAP = [
    "import json as _json",
    "from ugm import intake as _I, thread as _T, driver as _D",
    "from ugm import selftest as _S, execution as _X",
    "",
    "def _play_plan(goal_text):",
    "    '''Read a goal in the closed CNL, pursue it, and stream what the search did.'''",
    "    g, world = _S._blocks()",
    "    named = {}",
    "    for n in list(g.nodes):",
    "        lbl = g.attr(n, 'label')",
    "        if lbl in ('a', 'b', 'c') and g.kind(n) == 'block':",
    "            named.setdefault(lbl, n)",
    "    ev = []",
    "    try:",
    "        goal = _I.read_goal(g, goal_text)",
    "    except Exception as e:",
    "        return _json.dumps({'error': str(e)})",
    "    th = _T.open_thread(g, 'session')",
    "    r = _D.pursue(g, goal, th, world, trace=ev.append, max_steps=400)",
    "    out = {'error': None, 'events': ev, 'found': bool(r.get('found'))}",
    "    if r.get('found'):",
    "        _X.execute(g, r['workbench'], r['frame'])",
    "        after = []",
    "        for k in ('a', 'b', 'c'):",
    "            on = g.target(named[k], 'on')",
    "            after.append(k + ' is on ' + (g.attr(on, 'label') or 'the ground'))",
    "        out['after'] = after",
    "    else:",
    "        out['why'] = r.get('why', '')",
    "    return _json.dumps(out)",
    "",
    "def _play_ask(text):",
    "    '''Ask / why, over the pantry. A question is a goal; the plan is the proof.'''",
    "    g, _paul = _S._mortality_library()",
    "    th = _T.open_thread(g, 'session')",
    "    try:",
    "        reply = _I.respond(g, text, th, 'root')",
    "    except Exception as e:",
    "        return _json.dumps({'error': str(e)})",
    "    return _json.dumps({'error': None, 'reply': reply})",
    "",
    "def _play_selftest():",
    "    '''Run the engine's own verification, here, in front of you.'''",
    "    return _json.dumps({'error': None, 'report': _S.report()})",
    "",
  ].join("\n");

  // ── Pyodide loading ────────────────────────────────────────────────────────
  var pyodidePromise = null;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("could not load " + src)); };
      document.head.appendChild(s);
    });
  }

  function getPyodide(wheelUrl, say) {
    if (pyodidePromise) return pyodidePromise;
    pyodidePromise = (function () {
      say("Downloading the Python runtime (once)…");
      return loadScript(PYODIDE_BASE + "pyodide.js")
        .then(function () { return window.loadPyodide({ indexURL: PYODIDE_BASE }); })
        .then(function (py) {
          say("Installing the engine…");
          return py.loadPackage("micropip")
            .then(function () { return py.pyimport("micropip"); })
            .then(function (micropip) { return micropip.install(wheelUrl); })
            .then(function () { py.runPython(BOOTSTRAP); return py; });
        });
    })();
    return pyodidePromise;
  }

  // ── Rendering ──────────────────────────────────────────────────────────────
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function steps(container) { return container.querySelector(".ugm-steps"); }

  function clear(container) {
    var s = steps(container);
    while (s.firstChild) s.removeChild(s.firstChild);
  }

  function status(container, text) {
    clear(container);
    steps(container).appendChild(el("div", "ugm-status", text));
  }

  function card(container, icon, title, cls, detail) {
    var row = el("div", "ugm-step " + (cls || ""));
    row.appendChild(el("div", "ugm-step-icon", icon));
    var body = el("div", "ugm-step-body");
    body.appendChild(el("div", "ugm-step-title", title));
    if (detail) body.appendChild(el("div", "ugm-step-fact", detail));
    row.appendChild(body);
    steps(container).appendChild(row);
    requestAnimationFrame(function () { row.classList.add("ugm-step-in"); });
    return row;
  }

  function binds(on) {
    return Object.keys(on).sort().map(function (k) { return k + "=" + on[k]; }).join(", ");
  }

  // How one trace event reads. ⚠ `refuse` and `consider` are styled differently from
  // `imagine` on purpose: the first two are the machine THINKING about a move, the
  // third is it actually trying one. Collapsing them would hide the whole point —
  // that a forbidden action is never imagined at all.
  function render(container, e) {
    if (e.kind === "goal") {
      card(container, "◎", "Goal: " + e.goal, "ugm-step-goal",
           "wants " + e.wants.join(", ") + " · open: " + (e.open.join(", ") || "none"));
    } else if (e.kind === "refuse") {
      card(container, "⛔", "Refused " + e.action + "(" + binds(e.on) + ")",
           "ugm-step-check-no", "never imagined — " + e.because.join(", "));
    } else if (e.kind === "consider") {
      card(container, "·", "Considering " + e.action + "(" + binds(e.on) + ")", "",
           "relevance band " + e.band + (e.band >= 4 ? " — writes exactly what's missing" : ""));
    } else if (e.kind === "imagine") {
      card(container, "◐", "Imagined " + e.action + "(" + binds(e.on) + ")",
           "ugm-step-check-yes",
           e.open.length ? "still open: " + e.open.join(", ")
                         : "everything wanted is now true");
    } else if (e.kind === "found") {
      var plan = e.plan.map(function (p) { return p[0] + "(" + binds(p[1]) + ")"; });
      card(container, "✔",
           "Plan found — " + e.length + " step(s), " + e.imagined + " imagined",
           "ugm-step-answer", plan.join("  →  "));
    } else if (e.kind === "exhausted") {
      card(container, "✖", "No plan after imagining " + e.imagined, "ugm-verdict-no",
           e.unmet ? "still wanted: " + e.unmet : "");
    }
  }

  function animate(container, events, done) {
    var i = 0;
    (function next() {
      if (i >= events.length) { if (done) done(); return; }
      render(container, events[i++]);
      setTimeout(next, STEP_DELAY_MS);
    })();
  }

  // ── Running ────────────────────────────────────────────────────────────────
  function busy(container, on) {
    Array.prototype.forEach.call(container.querySelectorAll("button"),
                                 function (b) { b.disabled = on; });
  }

  function run(container) {
    var wheel = container.getAttribute("data-wheel");
    var mode = container.getAttribute("data-mode") || "plan";
    var input = container.querySelector(".ugm-corpus");
    var text = input ? input.value : "";

    busy(container, true);
    status(container, "Starting up…");

    getPyodide(wheel, function (m) { status(container, m); })
      .then(function (py) {
        clear(container);
        var raw;
        if (mode === "selftest") {
          raw = py.runPython("_play_selftest()");
        } else {
          py.globals.set("_arg", text);
          raw = py.runPython(mode === "ask" ? "_play_ask(_arg)" : "_play_plan(_arg)");
        }
        var out = JSON.parse(raw);

        if (out.error) {
          card(container, "✖", "Refused", "ugm-verdict-no", out.error);
          busy(container, false);
          return;
        }
        if (mode === "selftest") {
          var pre = el("pre", "ugm-step-fact", out.report);
          pre.style.whiteSpace = "pre-wrap";
          pre.style.overflowX = "auto";
          steps(container).appendChild(pre);
          busy(container, false);
          return;
        }
        if (mode === "ask") {
          out.reply.split("\n").forEach(function (line, n) {
            card(container, n === 0 ? "◎" : "·", line, n === 0 ? "ugm-step-answer" : "");
          });
          busy(container, false);
          return;
        }
        animate(container, out.events, function () {
          if (out.after) {
            card(container, "▣", "Carried out for real", "ugm-step-answer",
                 out.after.join(" · "));
          } else if (out.why) {
            card(container, "·", "Why not", "ugm-step-note", out.why);
          }
          busy(container, false);
        });
      })
      .catch(function (err) {
        status(container, "Something went wrong: " + (err && err.message ? err.message : err));
        busy(container, false);
      });
  }

  // ── Wiring (delegated, so it survives instant navigation) ──────────────────
  document.addEventListener("click", function (ev) {
    if (!ev.target.closest) return;
    var btn = ev.target.closest(".ugm-run");
    if (btn) {
      var c = btn.closest(".ugm-playground");
      if (c) run(c);
      return;
    }
    var quick = ev.target.closest(".ugm-ask");
    if (quick) {
      var c2 = quick.closest(".ugm-playground");
      if (!c2) return;
      var field = c2.querySelector(".ugm-corpus");
      if (field) field.value = quick.getAttribute("data-text") || field.value;
      run(c2);
    }
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter" || !ev.ctrlKey) return;
    var t = ev.target;
    if (!t.classList || !t.classList.contains("ugm-corpus")) return;
    var c = t.closest(".ugm-playground");
    if (c) { ev.preventDefault(); run(c); }
  });
})();
