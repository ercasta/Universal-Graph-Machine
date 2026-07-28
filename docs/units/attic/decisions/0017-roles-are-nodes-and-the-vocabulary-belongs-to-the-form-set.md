# 0017. Roles are nodes, and the vocabulary belongs to the form set

**Status — current (2026-07-28): HALF.** `../../model.md` §3 — roles are nodes, yes; the shared vocabulary belonging to a form set is deleted. Names are ordinary attributes.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §22.3, §22.5

## Context

`Fact.p` was a string, which made the predicate slot special: a predicate variable was
inexpressible, and a reserved hack existed so a predicate could occupy a node slot in a firing record.

## Decision

**Every slot is a node, including the predicate.** And role identity comes from the **form set**: a
`Vocabulary` mints roles once, at load.

> **A form may mint through the vocabulary; an utterance may not.**

## Evidence

- Three recorded problems dissolved at once: the predicate variable needs no new primitive (`?p` is
  an ordinary node variable); generic substitution becomes two atoms instead of a clause per template; and the
  name-equality hack has no exception left to guard.
- **Namelessness applies to roles exactly as to entities:** two independently minted `likes` nodes do not
  match. So a role cannot be minted per occurrence.
- **A registry keyed on a surface word and consulted at run time would be a second global structure** — it
  would fuse two utterances by name, which is the label this substrate abolished.

## Consequences

- An all-variable pattern is now *sayable*, and pays for it (`0025`).
- A novel role — a word no form supplies — is not resolved here at all. Relating it to known roles is the one
  job left for embeddings, and it is a much smaller claim than "everything becomes graded".
- The same distinction one level down licenses **lexemes**, which is what makes reference possible (`0026`).
