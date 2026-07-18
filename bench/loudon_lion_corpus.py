"""
CORPUS — Mrs. Loudon's *Entertaining Naturalist*, the LION entry, first 50 sentences VERBATIM.

Source: https://www.gutenberg.org/cache/epub/51166/pg51166-images.html (public domain).

PROTOCOL, and why it is this strict. The experiment asks whether UGM can learn rules from a real
book translated to CNL — but the translator is an LLM (me), which means the translator can
unconsciously keep the sentences that parse and drop the ones that do not, making any coverage
number meaningless. So:

  * the span is FIXED and CONTIGUOUS — 50 consecutive sentences from the start of the Lion entry,
    chosen before any translation was attempted;
  * EVERY sentence gets an entry here, in order, with its verbatim text;
  * a sentence that yields no CNL records WHY, and stays in the list. Nothing is silently dropped;
  * the translation is conservative: only what the sentence ASSERTS as classification or property.
    Figurative language ("king of beasts"), evaluation, hedged attribution ("some naturalists
    considered"), and narrative anecdote are NOT mined for facts, because doing so would be me
    inventing data.

TWO DISTINCT NUMBERS COME OUT OF THIS, and conflating them would hide the result:
  (a) TRANSLATABILITY — what fraction of a real book's sentences assert an extractable fact at
      all? This measures the SOURCE, not UGM.
  (b) INTAKE COVERAGE — of the CNL actually produced, what fraction does UGM recognise? This
      measures UGM.

Multi-word entities (`african lion`, `lion of guzerat`) are deliberately NOT sanitised into single
tokens, even though definite-article/noun-phrase merging is a known batch gap — sanitising them
would be tuning the corpus to the parser and would defeat the measurement.
"""

# (n, verbatim source sentence, [CNL lines], reason-if-empty)
SENTENCES: list[tuple[int, str, list[str], str]] = [
    (1, "The Lion is called the king of beasts, not only from his grave and majestic appearance, "
        "but from his prodigious strength.",
     ["the lion is strong"],
     ""),
    (2, "Zoologists describe him as an animal of the cat kind, distinguished from the other species "
        "of the genus by the uniformity of his colour, the mane which decorates the male, and a tuft "
        "of hair at the tip of the tail, which conceals a small prickle or claw.",
     ["the lion is a cat", "the lion has a mane", "the lion has a tail"],
     ""),
    (3, "Lions were formerly found in all the hot and warmer temperate parts of the whole world; but "
        "they are now confined to Africa, and some parts of Asia.",
     ["the lion lives in africa", "the lion lives in asia"],
     ""),
    (4, "The African Lion stands four or five feet high, and his body is from seven to nine feet long.",
     ["the african lion is a lion"],
     ""),
    (5, "The mane is thick, and somewhat curly; and the colour varies in different parts of Africa, "
        "but it is generally of a clear dark brown, deepening in some cases almost into black.",
     [],
     "asserts a property of the MANE, not of an animal, and the colour claim is hedged/variable"),
    (6, "The Asiatic Lions are smaller than those of Africa, and their colour paler.",
     ["the asiatic lion is a lion", "the asiatic lion is smaller than the african lion"],
     ""),
    (7, "The Bengal Lion is of a light brown, with a long flowing mane; the Persian Lion is of a sort "
        "of cream-colour, with a short thick mane; and the Lion of Guzerat is of a reddish brown, "
        "without any mane.",
     ["the bengal lion is a lion", "the bengal lion has a mane",
      "the persian lion is a lion", "the persian lion has a mane",
      "the guzerat lion is a lion", "the guzerat lion has no mane"],
     ""),
    (8, "These varieties have been considered as distinct species by some naturalists.",
     [],
     "hedged attribution about classification opinion, not an asserted fact"),
    (9, "All the varieties agree in their habits; they lie hid in jungles in the long grass, and when "
        "aroused either walk quietly and majestically away, or turn and look steadily at their pursuers.",
     ["the lion lives in jungles"],
     ""),
    (10, "Their roar is terrific: and in a wild state, the animal generally roars with his mouth close "
         "to the ground, which produces a low rumbling noise, like that of an earthquake.",
     ["the lion roars"],
     ""),
    (11, "The effect is described by those who have heard it, as making the stoutest heart quail; and "
         "the feebler animals, when they hear it, fly in dismay, often in their terror falling in the "
         "way of their enemy, instead of avoiding him.",
     [], "narrative description of an effect; no classification or property asserted"),
    (12, "Serpents, and some of the larger animals, will, however, fight with Lions, and occasionally "
         "kill them; and Lions, when pursued by man, are sometimes hunted with dogs, but are oftener "
         "shot, or speared.",
     [], "hedged and episodic ('occasionally', 'sometimes', 'oftener'); not a stable property"),
    (13, "Those which are exhibited in menageries have generally been caught in pits.",
     [], "about captured individuals, hedged ('generally'); not a species property"),
    (14, "The pit is dug where traces have been discovered of a Lion's path; and it is then covered "
         "with sticks and turf.",
     [], "narrative: describes a human trapping procedure"),
    (15, "He is deceived by the appearance of solidity presented by the turf, and attempts to walk over "
         "it; but the moment he sets his foot upon the covering of the trap, it breaks beneath his "
         "weight, and he falls into the pit.",
     [], "narrative continuation of the trapping procedure"),
    (16, "He is then kept without food for several days, shaking the ground with his roaring, and "
         "fatiguing himself by vainly attempting to escape; till, at last, he becomes exhausted, and so "
         "tame as to permit his captors to put ropes round him, and drag him out.",
     [], "narrative continuation"),
    (17, "He is then put into a cage, and removed in a kind of waggon, wherever his captors may wish to "
         "take him.",
     [], "narrative continuation"),
    (18, "The generosity of the Lion has been much extolled; but the tales related of it appear to have "
         "had no other foundation than the fact, that, like many other beasts, when gorged with food he "
         "will not attack a man.",
     [], "meta-commentary refuting a legend; the residual claim is conditional and hedged"),
    (19, "A great amount of courage has also been so generally ascribed to him that the expression \"as "
         "brave as a Lion,\" has become proverbial, and he has been regarded as a sort of symbol of that "
         "quality.",
     [], "about a proverb and reputation, not about the animal"),
    (20, "For this respectable character, the Lion is no doubt mainly indebted to his possession of a "
         "mane, and to the boldness of appearance produced by his carrying his head elevated; for in all "
         "other respects he is a genuine cat, with neither more nor less courage than belongs to the cats "
         "in general.",
     ["the lion is a cat"],
     ""),
    (21, "As the Lion belongs to the cat tribe, his eyes are incapable of bearing a strong light; it is "
         "therefore generally in the night that he prowls about for prey, and when the sun shines in his "
         "face, he becomes confused and almost blinded.",
     ["the lion is a cat", "the lion hunts at night"],
     ""),
    (22, "Lion hunters are aware of this fact.",
     [], "about hunters, not lions"),
    (23, "In the day-time they always consider themselves safe, so long as they have the sun on their "
         "backs.",
     [], "about hunters' beliefs"),
    (24, "In the night, a fire has nearly the same effect; and travellers in Africa and the deserts of "
         "Arabia can generally protect themselves from Lions and Tigers by making a large fire near "
         "their sleeping-place.",
     [], "advice to travellers; hedged ('nearly', 'generally')"),
    (25, "The strength of the African species is so great that he has been known to carry away a young "
         "heifer, and leap a ditch with it in his mouth.",
     ["the african lion is strong"],
     ""),
    (26, "The power that man may acquire over this animal has been often shown in the exhibitions of Van "
         "Amburgh, Carter, and others; but the attachment which Lions sometimes form for their keepers, "
         "was never more strongly exemplified than in the following anecdote.",
     [], "frame for an anecdote"),
    (27, "M. Felix, the keeper of the animals in Paris, some years ago, brought two Lions, a male and "
         "female, to the national menagerie.",
     [], "anecdote: particular historical individuals"),
    (28, "About the beginning of the following June he was taken ill, and could no longer attend them; "
         "and another person was under the necessity of performing this duty.",
     [], "anecdote"),
    (29, "The male, sad and solitary, remained from that moment constantly seated at the end of his cage, "
         "and refused to take food from the stranger, whose presence was hateful to him, and whom he "
         "often menaced by bellowing.",
     [], "anecdote"),
    (30, "The company even of the female seemed now to displease him, and he paid no attention to her.",
     [], "anecdote"),
    (31, "The uneasiness of the animal led to a belief that he was really ill; but no one dared to "
         "approach him.",
     [], "anecdote"),
    (32, "At length Felix recovered, and, with an intention to surprise the Lion, crawled softly to the "
         "cage, and showed his face between the bars: the Lion, in a moment, made a bound, leaped against "
         "the bars, patted him with his paws, licked his hands and face, and trembled with pleasure.",
     [], "anecdote"),
    (33, "The female also ran to him; but the Lion drove her back, and seemed angry, and fearful lest she "
         "should snatch any favours from Felix; a quarrel was about to take place, but Felix entered the "
         "cage to pacify them.",
     [], "anecdote"),
    (34, "He caressed them by turns; and was afterwards frequently seen between them.",
     [], "anecdote"),
    (35, "He had so great a command over these animals, that, whenever he wished them to separate and "
         "retire to their cages, he had only to give the order: when he wished them to lie down, and show "
         "strangers their paws or throats, they would throw themselves on their backs on the least sign, "
         "hold up their paws one after another, open their jaws, and, as a recompense, obtain the favour "
         "of licking his hand.",
     [], "anecdote"),
    (36, "The Lion, like all animals of the cat kind, does not devour his prey the moment he has seized it.",
     ["the lion is a cat"],
     ""),
    (37, "When those in cages are fed, they generally hide their food under them for a minute or two, "
         "before they eat it.",
     [], "about captive individuals, hedged ('generally')"),
    (38, "Thus an instance is known of a man, who was struck down by a Lion, having time to draw his "
         "hunting-knife and stab the ferocious beast, who was growling over him, to the heart, before it "
         "had seriously injured him.",
     [], "anecdote"),
    (39, "The Lion also resembles a cat in his mode of stealing after, and watching his prey, a long time "
         "before seizing it.",
     ["the lion is a cat"],
     ""),
    (40, "Dr. Sparrman mentions a singular instance of the animal's habits in this respect.",
     [], "frame for an anecdote"),
    (41, "A Hottentot perceiving that he was followed by a Lion, and concluding that the creature only "
         "waited the approach of night to make him his prey, began to consider what was the best mode of "
         "providing for his safety, and at length adopted the following:—Observing a piece of broken "
         "ground with a precipitate descent on one side, he sat down by the edge of it; and found, to his "
         "great joy, that the Lion also made a halt, and kept at a distance behind him.",
     [], "anecdote"),
    (42, "As soon as it grew dark, the man, sliding gently forward, let himself down a little below the "
         "edge of the steep, and held up his cloak and hat on his stick, at the same time gently moving "
         "them backward and forward.",
     [], "anecdote"),
    (43, "The Lion, after a while, came creeping towards the object; and mistaking the cloak for the man "
         "himself, made a spring at it, and fell headlong down the precipice.",
     [], "anecdote"),
    (44, "Many interesting anecdotes of Lions and Lion-hunting may be found in the accounts of their "
         "travels published by Gordon Cumming, Andersson, and Dr. Livingstone.",
     [], "bibliographic remark"),
    (45, "From the latter we may extract the following account of an escape literally from the very jaws "
         "of death:—\"Being about thirty yards off,\" says the doctor, \"I took a good aim at his body "
         "through the bush, and fired both barrels into it.",
     [], "quoted first-person narrative"),
    (46, "The men then called out, 'He is shot, he is shot!'",
     [], "quoted dialogue"),
    (47, "Others cried, 'He has been shot by another man too; let us go to him!'",
     [], "quoted dialogue"),
    (48, "I did not see any one else shoot at him, but I saw the Lion's tail erected in anger behind the "
         "bush, and turning to the people, said, 'Stop a little till I load again.'",
     [], "quoted narrative"),
    (49, "When in the act of ramming down the bullets I heard a shout.",
     [], "quoted narrative"),
    (50, "Starting and looking half round, I saw the Lion just in the act of springing upon me.",
     [], "quoted narrative"),
]


def cnl_lines() -> list[str]:
    """Every CNL line the translation produced, in source order (duplicates kept — the book
    restates `the lion is a cat` four times, and that repetition is real data)."""
    return [line for _n, _src, lines, _why in SENTENCES for line in lines]


def stats() -> dict:
    translated = [s for s in SENTENCES if s[2]]
    return {
        "sentences": len(SENTENCES),
        "sentences_yielding_facts": len(translated),
        "cnl_lines": len(cnl_lines()),
        "distinct_cnl_lines": len(set(cnl_lines())),
    }
