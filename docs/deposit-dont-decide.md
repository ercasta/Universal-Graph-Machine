# Deposit, don't decide

Three things were proposed for the engine to do automatically, with the proposer
noting they cut against the direction of making the engine stupid:

1. **memory** — the engine records what happened, rather than hoping rules track it;
2. **simulation** — given a cause-to-effect world model, roll it forward autonomously;
3. **discrepancy** — predict the result and deposit markers where the world disagrees.

All three are already built, and the reason they were allowed is worth stating,
because it is not *the engine must be stupid*.

> **The engine may compute anything whose result is a fact the rules can read,
> deny and argue with. What it may not do is decide.**

That is the same test the design applies to primitives: admissible if and only if
every decision it embodies can be an argument. Memory, prediction and discrepancy
all pass, because each of them ends in a deposit. Choosing which utterances to
believe, or which strategy applies, ends in a decision, and those stay in rules.

## 1. Memory — shipped, with one known gap

Every write goes through one gate and is stamped with locus, licence, source and
what it consumed. Nothing has to be tracked by a corpus: `why(p)` walks the
licences back to the roll that caused it, including a tool's answer, because a
tool's answer is a premise like any other.

The machinery also deposits what only it can know, and the list is long:
`arrived`, `emitted`, `answered`, `expects`, `exercised`, `spent`, `forgone`,
`close`, `defeated`, `quiet`, `blocked`, `bounded`, `widened`, `reached`.
Each is one fact and no interpretation.

**The gap, already recorded as debt rather than hidden.** `gate.reseat` moves a
frame to a later seat, and §17 says every seat move is a write — this one is not
yet an entry. So a walker or a `causes` rule advancing the register leaves no
record of the advance itself.

## 2. Simulation — the apparatus exists, the driver does not

`causes` is the cause-to-effect connective, and forward application already
deposits what it predicts. `Machine._expect`, on why this must be machinery:

> "Without the deposit there is nothing to be surprised against — an expectation
> that lives in an interpreter variable is unmatched not because the rule was
> weak but because there is nothing there to match."

What is missing is a **driver**: something that rolls the model forward without
acting and learns from where the predictions failed. The parts for that exist
too — `Machine.replay` mutes the boundary for a whole replay, so acts land as
`taken` and become `did` through the bundle and nothing leaves the agent. A
simulator is that muting plus a loop that never waits for the world.

**And there is a measured warning about when it is worth running.** On
`ugm.dungeon`, same seed and same corpus, one connective changed:

    causes    2.34s   1227 entries   74 moments   392 expects/deviates/close
    implies   0.31s    868 entries    1 moment     57

Twelve times the cost, and the fight reaches the identical verdict — because a
game's rules are never wrong, so the surprise apparatus is real work with nothing
to find. That is an argument **for** the proposal rather than against it:
prediction is dead weight exactly where the model is right, and is the whole
point where the model can be wrong. A learner is the second case; a rulebook is
the first. The choice of connective is therefore a claim about whether the model
is expected to be surprised.

## 3. Discrepancy — shipped, and split better than proposed

The proposal was that the engine deposit discrepancy markers. What is built
splits the job in two, and the split is the interesting part:

- **the engine deposits the expectation** — `expects(p, +)` per consequent
  member, as a mention, with a licence. Only the machinery can do this, because
  only it knows what a rule concluded forward.
- **rules notice the deviation** — four bundled rules, not a phase:

      rule <deviation-+-contradicted> = implies( { +expects(?p, plus),  -?p  }, { +deviates(?p) } )
      rule <deviation-+-invalidated>  = implies( { +expects(?p, plus),  ? ?p }, { +deviates(?p) } )
      rule <deviation---contradicted> = implies( { +expects(?p, minus), +?p  }, { +deviates(?p) } )
      rule <deviation---invalidated>  = implies( { +expects(?p, minus), ? ?p }, { +deviates(?p) } )

Noticing a deviation used to be a phase, and the note on its removal is the
argument in one line: *§18 already said surprise is a match, and the phase was
that sentence being false of the implementation.*

Two things fall out of doing it this way. §9's `?` — *I can no longer say* — is a
disappointed expectation exactly as much as *the opposite happened*, which a
hard-coded comparison would have had to be told. And a corpus can deny a
deviation rule, so what counts as a surprise is arguable rather than fixed.

## What this means for the ones still to build

The criterion gives a clean test for anything proposed next. A candidate belongs
in the engine if it **ends in a deposit** and the deposit is one fact with no
interpretation; it belongs in rules if it ends in a choice. By that test:

- recording a seat move — engine, and it is owed;
- driving a simulation — engine, since only the loop can mute the boundary;
- deciding *when* to simulate, or what a deviation means, or what to do about
  it — rules, every time.
