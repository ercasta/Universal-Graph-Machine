# Homoiconic grammar — the intake grammar as CNL data, interpreted by rules

> **Status: PROPOSED, spike not yet run (2026-07-18).** User proposal, arrived at from the
> book-corpus evidence: *"express the grammar in CNL and have rules that process the grammar to
> intake sentences in that grammar, instead of hardcoding forms."*
>
> Evidence base: `bench/spike_loudon.py` + `bench/loudon_lion_corpus.py` (50 verbatim sentences of
> Mrs. Loudon's *Entertaining Naturalist*). Companion: `learning_design.md` (the arc this
> unblocks), `../vision.md` §10 (what was rejected, and why this is not that).

## 1. Half of it already exists, and is proven

The project ALREADY does "grammar as CNL data → rules generated from it", for **word classes**:

```
X is a relation     X is a determiner     X is a variable     X is an auxiliary
```

`forms.surface_forms` and `authoring.relation_forms` GENERATE recognition rules from those
declarations at runtime (`declared_*` unions the user's declarations with the default closed-class
sets). This is not hypothetical — measured 2026-07-18:

```
"the lion lives in africa"                       -> ('lives','is','lion'), ('lives','in','africa')   GARBAGE
"lives_in is a relation" + "the lion lives_in africa" -> ('lion','lives_in','africa')                CORRECT
```

A declaration fixed a mis-parse with no code change.

**What is hardcoded is COMPOSITION** — how constituents combine. `FORM_RULES` / `FACT_FORMS`
enumerate specific surface shapes, so a sentence outside them either fails (`the lion roars` —
intransitive, only two slots) or is absorbed by a neighbouring pattern and folds to nonsense.

So the proposal is not a rewrite. It extends an established, working gradient from CLASSES to
COMPOSITION — and it is the same homoiconic move the project keeps making (ISA programs as data,
`form KEY :` as data, rules-as-graph-data in the learning arc). It introduces no new KIND of thing.

## 2. This is not the rejected PCFG (but it inherits the crux)

Vision §10 rejected the PCFG **grammar structure** (terminals/non-terminals) and **probability as a
branch selector**, on this ground:

> control is now token-passing, not branch-selection: every enabled rule fires; nothing *selects* a
> branch

A declarative, NON-probabilistic composition grammar is not that. But the reason for the rejection
is exactly the crux below, so the distinction must not be used to wave the problem away.

## 3. THE CRUX — ambiguity, and the no-branch-selection commitment

A real grammar yields multiple parses. The engine's core commitment is that every enabled rule
fires and nothing selects a branch, so **two competing parses would both fire and write
contradictory facts**. Ambiguity demands selection; selection is what was rejected.

**Proposed answer: do not select — REFUSE AND ASK.** Ambiguity becomes a discriminating question
("two readings; which did you mean?"), preserving the no-branch-selection commitment and reusing
the `can_ask` wait-set. This is the FOURTH independent time that shape has fallen out of this work
(k>=2 licensing, the sparse-KB bootstrapping paradox, discrepancy contrast, now parsing), which is
some evidence it is the architecture rather than a coincidence.

This must be settled by the spike, not assumed.

## 4. The strongest argument: the current failure mode is a SILENT MIS-PARSE

`('lives','is','lion')` is the form bank GUESSING instead of REFUSING. The line routed as success
and wrote nonsense — strictly worse than the unrecognized case it replaced.

That is the same defect class as S1 and S1b (`learning_design.md` §9, §9.1), which this session
spent its time eliminating: *quietly does something wrong* rather than *says it does not know*. A
declared grammar can answer "does not conform"; a bank of independent surface patterns structurally
cannot, because there is no notion of the whole sentence being accounted for.

## 5. What the spike must find out (wall-first)

1. **Ambiguity.** Does refuse-and-ask work, or does the graph fill with half-parses? Can "this
   sentence has two readings" even be DETECTED with rules that all fire, or does detection itself
   need a selector?
2. **Cost.** A rule-interpreted grammar per sentence, against the ~12ms/utterance budget. Intake
   normalization alone already cost 7.1 → 11.2 ms.
3. **Coverage on the residual failures**, which are the real target: intransitive (`the lion
   roars`), negation (`has no mane` — the exception-bearing construction), comparative
   (`is smaller than`), prepositional with an undeclared verb.
4. **Does it subsume the existing forms**, or sit alongside them? A grammar that cannot express
   what `FACT_FORMS` already does is a second system, not a replacement.

## 6. Why it matters beyond parsing

- **Exceptions.** Negation is the construction that carries them (§ plan, "partial intake coverage
  is not neutral"). Until it parses, the defeasible-exception work has no data.
- **Form learning (T3).** Learning a form becomes learning a COMPOSITION rather than a whole
  template, which is a far smaller and better-posed induction problem — and the discriminating
  question already exists to disambiguate it.
- **Loudness.** "Does not conform" is a diagnostic the current architecture cannot produce.

## 7. Known tension to resolve

Multi-word noun phrases currently DECOMPOSE by design (`the african lion` → head `lion` +
`lion is african`, never an `african_lion` entity — `forms.py` §2, "structure exposed to reasoning,
not hidden in an opaque string"). Measured consequence on a taxonomy corpus: every subspecies
collapses onto ONE `lion` node, so `lion has mane` (from the Bengal lion) and the Guzerat lion's
manelessness would land on the SAME entity — a contradiction manufactured by the grammar, not by
the source. Whether composition should be able to MINT a distinct entity is a real question the
grammar arc has to answer.
