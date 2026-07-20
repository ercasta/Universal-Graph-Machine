# Loudon residue log — the first one

Output of the REFUSAL EXPERIMENT, 2026-07-20. A cold-context LLM was given only the
comment-stripped form set (`corpus/loudon_grammar.cnl`, declarations only) and the 50 verbatim
sentences of `loudon_lion_corpus.py`, under the protocol: every sentence yields CNL,
NOTHING-TO-ASSERT, or CANNOT-EXPRESS — never silence.

**Why this file exists.** `design/form_inventory.md` §5 says the residue log IS the concept
inventory, generated rather than audited by hand. This is that log's first entry, and it is the raw
evidence behind §4's table. Without it the inventory is an assertion; with it, it is derived.

**Headline result** (analysis in `implementation_plan.md`, the refusal-experiment block):
CNL 3 / CANNOT-EXPRESS 26 / NOTHING-TO-ASSERT 21, against the hand translation's 13 CNL. **Zero
manufactured facts; every produced line parses; all 10 disagreements run the same way — the agent
refused where the human extracted, never the reverse.** The contract held; the open question is
whether ATTENUATION should be permitted (see §5 of the design doc, and the four-outcome contract
this experiment produced).

⚠ Two of the 26 refusals (10, 21) were caused by DEFECTS IN THE FORM SET, not by its limits — the
hedged intransitive and hedged prepositional shapes were missing. Both were fixed the same day; this
log records the state at the time of the run.

---

## CNL produced — with residue (the four-outcome contract, invented spontaneously by the agent)

| # | CNL | residue — what was dropped |
|---|---|---|
| 6 | `the asiatic lion is smaller than the african lion` | second conjunct "their colour paler" — no noun *colour*, no comparative *paler* |
| 7 | `the guzerat lion has no mane` | three colour claims (light brown / cream / reddish brown); mane descriptions "long flowing" / "short thick" |
| 25 | `the african lion is strong` | resultative "so great that he has been known to carry away a young heifer, and leap a ditch with it in his mouth" |

## CANNOT-EXPRESS — 26 entries, with what was missing

| # | missing |
|---|---|
| 1 | naming predicate *is called*; nouns king/beasts/appearance/strength; causal *from*. (The strength is a PRESUPPOSITION here, not the assertion.) |
| 2 | attribution frame (*zoologists describe him as*); nouns genus/species/colour/male/hair/tip/claw; *distinguished from*. `the lion is a cat` is sayable but the sentence asserts what zoologists SAY. |
| 3 | tense (*formerly* / *now*); *confined to* (exclusivity — the language has no *only*); *parts of*; conjunction of two locations |
| 4 | numerals; units of measure; height/length predicates |
| 5 | adjectives thick/curly/dark/black; noun *colour*; verb *varies*; degree/exception modifiers |
| 8 | attribution (*some naturalists have considered*); nouns variety/species; adjective *distinct* |
| 9 | universal quantifier over varieties; *agree in habits*; verbs lie/hide/walk/turn/look; noun *grass*; disjunction *either…or*; manner adverbs |
| 10 | *wild state*; *with his mouth close to the ground*; *produces a noise*; simile. **Also structural: a hedged INTRANSITIVE licensed no assertion** (defect, since fixed) |
| 11 | reported-speech frame; nouns heart/animals/terror/enemy; verbs quail/fly/fall/avoid; superlative *stoutest* / comparative *feebler* |
| 12 | nouns serpent/animal/man/dog; verbs fight/kill/shoot/spear; passive voice; comparative frequency *oftener*. Hedges exist but nothing they could attach to does |
| 13 | nouns menagerie/pit; verbs exhibit/catch; passive voice; past tense; relative clause *those which* |
| 14 | nouns pit/trace/path/sticks/turf; verbs dig/discover/cover; passive voice; locative subordinator *where* |
| 15 | verbs deceive/attempt/walk/set/break/fall; nouns solidity/turf/foot/trap/weight/pit; temporal subordination |
| 16 | verbs keep/shake/fatigue/escape/become/permit/put/drag; nouns food/days/ground/ropes/captors; resultative *so tame as to*; temporal *till at last* |
| 17 | nouns cage/waggon/captors; verbs put/remove/wish/take; free relative *wherever* |
| 18 | verbs attack/gorge/extol; nouns generosity/tales/foundation/man/food; temporal conditional *when gorged*; **general verbal negation** (the language can only deny via a negated object of *has*) |
| 19 | noun *courage*; verb *ascribe*; metalinguistic reference to an expression; *proverbial*; *symbol*; degree *a great amount of* |
| 20 | nouns courage/character/head; *neither more nor less than*; causal *indebted to*; restrictor *in all other respects* |
| 21 | causal connectives *as* / *therefore*; nouns eyes/light/sun/prey/tribe; verbs bear/prowl/shine/become. **Also structural: a hedged clause had no prep/pobj slot** (defect, since fixed) |
| 22 | noun *hunter*; propositional attitude *are aware of*; anaphoric reference to a preceding fact |
| 23 | nouns day-time/sun/backs; adjective *safe*; verb *consider*; quantifier *always*; conditional *so long as* |
| 24 | nouns fire/travellers/deserts/arabia/tigers/sleeping-place; verb *protect*; instrumental *by making*; *nearly the same effect* |
| 26 | nouns power/attachment/keeper/exhibitions/man; verbs acquire/show/form/exemplify; proper names; superlative *never more strongly than* |
| 36 | verbs devour/seize; noun *prey*; temporal *the moment*; comparison *like all animals of the cat kind*; **general verbal negation** |
| 37 | nouns cage/food; verbs feed/hide/eat; temporal clauses *when* / *before*; duration *a minute or two* |
| 39 | verb *resembles* — DISTINCT from the copula (`the lion is a cat` would say something different); nouns prey/mode; verbs steal-after/watch/seize; duration *a long time* |

## NOTHING-TO-ASSERT — 21 entries

27–35, 38, 40–50. Anecdote (27–35, 38, 41–43), bibliographic remark (40, 44), quoted first-person
narrative or dialogue (45–50). This is the SOURCE's property — the 26%-translatability finding —
not a limit of the form set.

---

## What the log says when sorted (feeds `form_inventory.md` §4)

Counting only what recurs, and separating the two types the design doc distinguishes:

**FUNDAMENTAL (needs a representation), by frequency:**
- **tense / aspect** — 3, 13, 14, 16, and implicit in most narrative. NO MECHANISM.
- **general verbal negation** — 18, 36. Today only `has` + negated object. Partial mechanism.
- **attribution / reported speech** — 2, 8, 11, 22, 23. Mechanism exists (pencil scope), unbuilt.
- **quantification** — 9 (*all the varieties*), 8 (*some naturalists*), 23 (*always*). Partial.
- **causation** — 1 (*from*), 20 (*indebted to*), 21 (*as / therefore*). NO MECHANISM.
- **exclusivity** — 3 (*confined to*). CWA/NAF exist; no surface.
- **conditionality / temporal subordination** — 15, 16, 18, 23, 37. Rule layer exists, unbuilt.
- **resemblance-in-a-respect** — 39, and it caused a real distortion in the hand translation.
  NO MECHANISM, and conflating it with `is_a` is the failure Brachman named.
- **degree beyond the comparative** — 11, 19, 26 (superlatives), 12 (*oftener*).

**BAROQUE (desugar), by frequency:**
- **passive voice** — 12, 13, 14. Reducible to active.
- **relative clauses** — 13 (*those which*), 14 (*where*), 17 (*wherever*).
- **conjunction of arguments** — 3, 6, 9. Reducible to repeated assertions.
- **manner adverbs, similes, resultatives** — 9, 10, 16, 25. Mostly attenuable as residue.

**The single biggest lever is not a construction at all: VOCABULARY.** Nearly every entry above
leads with missing nouns and verbs. The form set has 30 words. That is a different kind of gap from
either column — it is neither baroque nor fundamental, it is just *absent*, and open-vocabulary mode
(`compile_grammar(open_class=…)`) already exists to address it at the cost of refusal. Deciding
whether to use it is an open question this log makes concrete.
