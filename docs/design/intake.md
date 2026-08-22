# `intake.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Deciding what a mention denotes -- intake, as rules.

    python -m ugm.probes.intake

`ugm/rules/intake.ugm` is the corpus. This runs it and holds it to the claims it
is here to make.

## Why this exists

Identity in this engine has always been decided by CONSTRUCTION. `Loader.atom`
keeps a table per name-scope, so `paul` written in two statements is one node,
and `text.py` says why that is right: *a corpus is a bound, `kettle` means one
node inside it, by construction and not by inference, which is why coreference
does not arise in authored knowledge at all.*

It does arise the moment anything arrives. *A man walked in; a man sat down* is
two mentions that may or may not be one man, and intake cannot know. So the
question this corpus answers is the one authored knowledge never had to ask.

## The layering, and the thing it buys

    mention      an event of speaking. Two mentions are NEVER one mention:
                 they have their own times and their own speakers, and a
                 rule may want to talk about the saying rather than the said.
    entity       what is spoken about.
    denotes      the reading -- an ordinary claim, concluded by a rule and
                 deniable by another.

⭐⭐⭐ **Coreference needs no identity merge.** Two mentions corefer when they
denote one entity, and that is two ordinary facts. Nothing is merged, nothing is
repointed, and retracting the reading is denying one fact rather than replaying
history. The engine's `merge` stays for the genuinely different case -- two
ENTITIES turning out to be one thing, the morning star and the evening star --
where congruence is what you want and the cost of getting it is warranted.

⭐⭐ **And a proper name is a mention like any other.** `grish` picks the same
goblin out that *the goblin you attacked three turns ago* picks out, through the
same relation, read by a rule of the same shape. That is the asymmetry this is
here to remove: today a name is stamped on the node and decides identity, while
every other way of denoting the same thing is a claim.

## What the engine supplies, and it is one thing

**`count`.** *The* goblin is *exactly one thing satisfies this description* --
a claim about the SET of readings, and a rule sees one binding at a time. So
the machinery answers it and the corpus decides what the number means: one is a
reference, two is an ambiguity to report, zero is a description that fits
nothing. No notion of a definite article anywhere in Python.

 **Asked at `quiet`**, because a count is true of a moment -- the same reason
`unsupported` waits for it.

 **But `quiet` means *nothing more applies to the mind I currently have*, not
*the search is complete*.** With `<bare>` dormant this corpus counts **0** where
it counted 2, and says `fits_nothing(m3)` -- benign, because nothing is left to
read m3 with. On a variant carrying a second denoting rule the same narrowing
counts **1** and the agent *resolves* m3 rather than reporting the ambiguity:
not less certain, **confidently wrong**. Which happens is the corpus's business.

⭐ That is the honest meaning of an aggregate rather than a hole to be patched.
`counted(..., 1)` is *one, among what I decided to consider*, and there is no
unnarrowed view to compare it with. The engine must not annotate it -- the
narrowing is a judgement the agent made, and `dormant(<r>)` is already an
ordinary dated claim, so *what was in mind* is answerable without any help.
