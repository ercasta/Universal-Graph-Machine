/*
 * The live playground — run the real engine in your browser.
 *
 * Loads Pyodide on demand, installs the pure-Python `ugm` wheel with micropip,
 * and runs the actual engine. No server, no backend, no re-implementation.
 *
 * Two modes:
 *
 *   corpus    — load a corpus, run the loop to quiescence, print what became of
 *               what was asked for, and answer `why` questions. This is exactly
 *               what `python -m ugm <file> --why ...` does, and it goes through
 *               the same two functions.
 *   selftest  — run `ugm.selftest`, here, in front of you.
 *
 * Everything printed was already in the graph before it was printed: `report()`
 * and `why()` read the same structures a rule reads. There is no explanation
 * subsystem to disagree with the engine.
 *
 * Document-level event delegation keeps this working under Material's
 * `navigation.instant` (SPA-style) page swaps.
 */
(function () {
  "use strict";

  var PYODIDE_VERSION = "0.26.4";
  var PYODIDE_BASE =
    "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_VERSION + "/full/";

  // ── The Python side, defined once after install ────────────────────────────
  //
  // Returns a JSON string rather than a proxy object — proxies across the
  // JS/Python boundary are fiddly, and this is a one-way report.
  var BOOTSTRAP = [
    "import io as _io, json as _json",
    "from contextlib import redirect_stdout as _redirect",
    "from ugm.machine import Machine as _Machine",
    "from ugm.text import load as _load, _report_unwebbed",
    "from ugm import selftest as _selftest",
    "",
    "def _play_corpus(src, asks):",
    "    '''Load, run to quiescence, report, and answer `why`.'''",
    "    m = _Machine()",
    "    notes = _io.StringIO()",
    "    try:",
    "        with _redirect(notes):",
    "            kb = _load(m, src)",
    "            _report_unwebbed(m)",
    "    except Exception as e:",
    "        return _json.dumps({'error': type(e).__name__ + ': ' + str(e)})",
    "    steps = m.run(limit=400)",
    "    out = {'error': None,",
    "           'notes': [l for l in notes.getvalue().splitlines() if l.strip()],",
    "           'ticks': len(steps),",
    "           'state': steps[-1].state if steps else 'nothing to do',",
    "           'report': list(m.report()),",
    "           'why': []}",
    "    for q in (asks or '').splitlines():",
    "        q = q.strip()",
    "        if not q:",
    "            continue",
    "        try:",
    "            lines = m.why(kb.term(q))",
    "        except Exception as e:",
    "            out['why'].append({'q': q, 'lines': ['could not read that: ' + str(e)]})",
    "            continue",
    "        # A proposition nothing concluded has no trail, and saying so IS the",
    "        # answer rather than an empty list.",
    "        out['why'].append({'q': q,",
    "                           'lines': lines or ['nothing concluded it']})",
    "    return _json.dumps(out)",
    "",
    "def _play_selftest():",
    "    '''Run the engine's own verification, here, in front of you.'''",
    "    buf = _io.StringIO()",
    "    try:",
    "        with _redirect(buf):",
    "            _selftest.main()",
    "    except Exception as e:",
    "        return _json.dumps({'error': type(e).__name__ + ': ' + str(e),",
    "                            'report': buf.getvalue()})",
    "    return _json.dumps({'error': None, 'report': buf.getvalue()})",
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
    if (detail) {
      var d = el("div", "ugm-step-fact", detail);
      d.style.whiteSpace = "pre-wrap";
      body.appendChild(d);
    }
    row.appendChild(body);
    steps(container).appendChild(row);
    requestAnimationFrame(function () { row.classList.add("ugm-step-in"); });
    return row;
  }

  function block(container, text) {
    var pre = el("pre", "ugm-step-fact", text);
    pre.style.whiteSpace = "pre-wrap";
    pre.style.overflowX = "auto";
    steps(container).appendChild(pre);
  }

  // ── Running ────────────────────────────────────────────────────────────────
  function busy(container, on) {
    Array.prototype.forEach.call(container.querySelectorAll("button"),
                                 function (b) { b.disabled = on; });
  }

  function renderCorpus(container, out) {
    // The load-time notes come first, because a corpus with a hole in it is
    // usually the answer to whatever the reader was about to be confused by.
    out.notes.forEach(function (n) {
      card(container, "·", "At load", "ugm-step-note", n);
    });

    var ended = out.ticks + " tick(s), ended " + out.state;
    card(container, out.state === "quiescent" ? "◼" : "⏱", ended,
         out.state === "quiescent" ? "ugm-step-answer" : "ugm-verdict-no",
         out.state === "applied" ? "stopped at the tick limit; it had not finished" : "");

    if (out.report.length) {
      card(container, "◎", "What became of what was asked for", "ugm-step-goal");
      block(container, out.report.join("\n"));
    }

    out.why.forEach(function (w) {
      card(container, "?", "why " + w.q + "?", "ugm-step-check-yes");
      block(container, w.lines.join("\n"));
    });
  }

  function run(container) {
    var wheel = container.getAttribute("data-wheel");
    var mode = container.getAttribute("data-mode") || "corpus";
    var corpus = container.querySelector(".ugm-corpus");
    var asks = container.querySelector(".ugm-asks");

    busy(container, true);
    status(container, "Starting up…");

    getPyodide(wheel, function (m) { status(container, m); })
      .then(function (py) {
        clear(container);
        var raw;
        if (mode === "selftest") {
          raw = py.runPython("_play_selftest()");
        } else {
          py.globals.set("_src", corpus ? corpus.value : "");
          py.globals.set("_asks", asks ? asks.value : "");
          raw = py.runPython("_play_corpus(_src, _asks)");
        }
        var out = JSON.parse(raw);

        if (out.error) {
          card(container, "✖", "Refused", "ugm-verdict-no", out.error);
          if (out.report) block(container, out.report);
          busy(container, false);
          return;
        }
        if (mode === "selftest") {
          block(container, out.report);
        } else {
          renderCorpus(container, out);
        }
        busy(container, false);
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
    // A preset swaps both fields in and runs, so a reader can try a listed
    // example without retyping it.
    var preset = ev.target.closest(".ugm-preset");
    if (preset) {
      var c2 = preset.closest(".ugm-playground");
      if (!c2) return;
      var corpus = c2.querySelector(".ugm-corpus");
      var asks = c2.querySelector(".ugm-asks");
      if (corpus && preset.getAttribute("data-corpus") !== null) {
        corpus.value = preset.getAttribute("data-corpus");
      }
      if (asks && preset.getAttribute("data-asks") !== null) {
        asks.value = preset.getAttribute("data-asks");
      }
      run(c2);
    }
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter" || !ev.ctrlKey) return;
    var t = ev.target;
    if (!t.classList) return;
    if (!t.classList.contains("ugm-corpus") && !t.classList.contains("ugm-asks")) return;
    var c = t.closest(".ugm-playground");
    if (c) { ev.preventDefault(); run(c); }
  });
})();
