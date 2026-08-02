# Reference: modules

The package is `ugm`. Every module is importable on its own, and there is no framework to
initialise — a `Graph` and whatever you load into it is the whole of the state.

```python
from ugm.graph import Graph
from ugm import asm, types, intake, thread, driver, query
```

## Substrate

| module | what it is | main entry points |
|---|---|---|
| `graph.py` | mutable nodes, named edges with ordered targets, edge properties, references, a maintained reverse index, an undo journal | `Graph`, `mint`, `link`, `at`, `attr`, `sources`, `savepoint`, `rollback`, `commit`, `Ref` |
| `focus.py` | named heads pointing into the graph — the control mechanism that replaces matching | `Focus` (`open`, `move`, `back`, `follow_ref`, `fork`, `spread`, `close`) |
| `path.py` | the one reference language: named hops, indices, backward hops, reach | `parse`, `resolve`, `node_at`, `value_at`, `via`, `reaches`, `render` |
| `types.py` | a type is a subgraph schema, declared as graph data; validation, never dispatch | `declare_type`, `Req`, `AttrReq`, `Rel`, `is_a`, `violations`, `subsumes`, `recognize`, `instances` |
| `hypothesis.py` | a hypothesis is an ordinary node with ordinary subgraphs under it | `open_hypothesis`, `assume`, `variant`, `backup`, `restore`, `conclude`, `rivals` |

## Programs

| module | what it is | main entry points |
|---|---|---|
| `isa.py` | the instruction set over named edges, focus heads and references; `run` is a loop over `tick` | `Machine`, `run`, `R`, `F`, `I` |
| `activation.py` | the interpreter's own state as graph data — program counter, stack, registers, focus | `open_activation`, `pc`, `push`, `pop`, `register`, `minted`, `chain`, `doing`, `retire` |
| `function.py` | a rule is a function — a named program with typed parameters, stored in the graph | `define`, `invoke`, `load`, `catalogue`, `producers`, `param_types`, `mocks_of`, `applicable` |
| `asm.py` | the text surface and language-model border; `.mf` files | `parse`, `unparse`, `load_text`, `load_file`, `load_dir`, `dump` |
| `native.py` | primitives the kernel executes but does not know; a table it does not populate | `register`, `call`, `names` |
| `dispatch.py` | the one place an effect leaves the graph, and the checkpoint guarding it | `register`, `service`, `forbid`, `veto_reason`, `Vetoed`, `Imagined` |

## Goals, planning and acting

| module | what it is | main entry points |
|---|---|---|
| `goal.py` | a wanted state as constraint nodes; the unmet ones drive planning | `open_goal`, `require_link`, `require_attr`, `require_type`, `require_known`, `forbid_action`, `require_action`, `limit_steps`, `unmet`, `satisfied`, `witnesses`, `blocked_on_ignorance`, `close_goal` |
| `plan.py` | backward chaining over return types into a lazy chain | `plan`, `calls_of`, `describe`, `run` |
| `workbench.py` | imagining on a copy — frames, mappings, forking, backtracking | `open_workbench`, `step`, `fork`, `frames`, `mappings`, `resolve`, `deviates`, `predicted_changes`, `fragile_steps` |
| `search.py` | the planner's own working memory as graph data — frontier, visited set, refusals | `open_search`, `offer`, `frontier`, `take_best`, `mark_seen`, `refuse`, `blocked_by` |
| `driver.py` | the outer loop — pursue a goal by imagining; effects read off rule bodies | `pursue`, `carry_out`, `follow`, `attempt`, `step`, `proposals`, `establishes`, `reads`, `relevance`, `Call` |
| `execution.py` | following a plan for real — replay, divergence, contingencies, recovery | `execute`, `path_to`, `step`, `alternatives`, `matching_alternative`, `resume`, `replan`, `recover`, `report` |
| `selection.py` | candidates, ranking, applying one function at a time | `candidates`, `score`, `rank`, `step`, `run_until_settled` |
| `loop.py` | one ordered agenda over every steppable task, one primitive step per tick | `open_loop`, `schedule`, `agenda`, `tick`, `run`, `verb_of`, `advance` |

## Deliberation

| module | what it is | main entry points |
|---|---|---|
| `guideline.py` | authored preference that reorders and never excludes | `prefer`, `avoid`, `advice`, `applies`, `ranker`, `governing` |
| `method.py` | an authored decomposition, as data, that selects itself | `method`, `step`, `draw`, `applicable`, `matches`, `decompose` |
| `criterion.py` | expert judgement as an ordered list, authored as text | `declare`, `wants`, `draw`, `test`, `does`, `speaks`, `decide`, `governing`, `disagreements` |
| `consequent.py` | the one tagged right-hand side shared by the families that have one | `achieve`, `call`, `of`, `kind`, `bindings_of` |
| `norm.py` | a prohibition that can be defeated, arbitrated as data | `declare`, `norms`, `outranks`, `settle`, `apply`, `explain` |
| `conflict.py` | contradictory goals, and interference between goals over one slot | `interference`, `plan_claims`, `interference_between`, `unsatisfiable`, `conflicts_on` |

## Memory, time and language

| module | what it is | main entry points |
|---|---|---|
| `thread.py` | materialised short-term memory — attention shifts and applications, in order | `open_thread`, `attend`, `applied`, `entries`, `previous`, `why`, `past`, `find_back`, `last_touching`, `connect` |
| `application.py` | applications and episodes — the record of what the system did | `open_episode`, `record`, `steps`, `applied_to`, `has_been_applied`, `generalise`, `compile_episode` |
| `memory.py` | what was seen, and whether the agent was the cause | `observe`, `sightings`, `believed`, `transitions`, `attribute`, `volatility`, `record_sighting` |
| `clock.py` | time as a node that points at what it dates | `moment`, `now`, `stamp`, `dated`, `follows`, `precedes`, `ordered` |
| `discourse.py` | what was said, in order, and what was later taken back | `speaker`, `say`, `utterances`, `retract`, `is_withdrawn`, `live`, `authority`, `ask`, `pending` |
| `forget.py` | the slower clock — keep what cannot be re-derived, sweep the rest | `roots`, `keepers`, `doomed`, `kept_because`, `compact`, `open_forgetting`, `step` |

## The border

| module | what it is | main entry points |
|---|---|---|
| `intake.py` | the controlled language — goals, types, advice, methods, criteria, questions | `read`, `read_goal`, `respond`, `resolve`, `forms_for`, `Unreadable`, `Ambiguous` |
| `query.py` | asking, which is a goal like any other | `ask`, `settle`, `why`, `explain`, `account`, `is_pure`, `refutes`, `derivations` |
| `locate.py` | *what* / *where* / *when* — locating a thing in an order the world already has | `what`, `where`, `when`, `locate`, `describe` |

## Other files

| path | what it is |
|---|---|
| `rules/*.mf` | the knowledge base on disk, in the assembly surface |
| `selftest.py` | the verification runner — `python -m ugm.selftest` |
