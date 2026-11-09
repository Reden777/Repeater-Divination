Are the lines' judgements (the sentences) all accurate?

**They are largely faithful to the Wilhelm–Baynes translation, but I would not certify them as an entirely exact or complete transcription.** The wording is recognizably from that translation—not a collection of invented interpretations.

It helps to distinguish **the accuracy of the sentences** from **whether your program displays them for the correct hexagram**.

### 1. The ordinary line texts look substantially correct

The entries I checked match Wilhelm–Baynes closely, allowing for punctuation, capitalization, and occasional wording changes. Their list order is also the conventional **bottom line first, top line last**.

For example, the unusual language about the marrying maiden “as a slave” in hexagram 54, line 3, and the goose approaching “cloud heights” in hexagram 53, line 6, really does appear in that translation. Those are not programming or transcription mistakes. [Sources: hexagrams 53–54](https://www.dankalia.com/delloro/361/index_files/wilhelm.html)

**However, I have not completed an edition-specific, word-for-word audit of all 384 ordinary line statements.** “Largely accurate” is justified; “every sentence verified” would not be.

### 2. There is at least one wording change worth correcting

**Hexagram 29, line 3** ends in your script with:

> “Do not act.”

The reference text ends with:

> “Do not act in this way.”

That is a small but potentially meaningful distinction: avoiding the action described versus a blanket instruction not to act. For fidelity to the reference, restore **“in this way.”** [Reference text hosted by Columbia](https://ccnmtl.columbia.edu/services/dropoff/china_civ_temp/week02/pdfs/iching.pdf)

This does not make your version wholly wrong, but it is not an exact transcription.

### 3. The two special all-changing statements are missing

Beyond the six ordinary line statements, hexagrams 1 and 2 have special statements:

| Hexagram | Condition | Wilhelm–Baynes statement |
|---|---|---|
| 1 — The Creative | All six lines are old yang, value 9 | “There appears a flight of dragons without heads. Good fortune.” |
| 2 — The Receptive | All six lines are old yin, value 6 | “Lasting perseverance furthers.” |

Your database does not contain these, and `cast()` does not handle them. [Reference](https://www.dankalia.com/delloro/361/index_files/wilhelm.html)

**These should be separate fields**, not seventh elements in the ordinary `lines` lists. How they take precedence over the ordinary statements should follow the interpretation convention you choose.

### 4. Hexagram 2’s overall judgement is incomplete

This is separate from its six line statements, but relevant if you mean all the oracle sentences.

Your `judgement` field includes only the opening about success and the perseverance of a mare. It omits the rest concerning:

- Undertaking something and trying to lead versus following and finding guidance.
- Finding friends in the west and south, and foregoing friends in the east and north.
- Quiet perseverance bringing good fortune.

That is a substantial abridgement, not merely punctuation or modernization. [Full judgement](https://www.dankalia.com/delloro/361/index_files/wilhelm.html)

**Bottom line:** The line texts appear substantially sound as Wilhelm–Baynes material, but the database is **not fully exact or complete**. Choose a specific published edition as your reference before treating every wording difference in online copies as an error.
