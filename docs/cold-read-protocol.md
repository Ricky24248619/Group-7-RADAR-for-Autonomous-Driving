# Cold read — P-6 and DS-4

**Story DZ-S3-1 / A4 · owner Damien Zhang · reviewer Fariya Zehrin · 24 September 2026**

P-6: *"A reader unfamiliar with the project can identify the key finding without
narration."* DS-4: *"when read by someone who has not used the dataset, they can state
what it can and cannot answer."*

Both have been open since Sprint 1 and **neither has ever been performed**. This is the
last acceptance condition on DZ-S3-1 and the one the document cannot satisfy by itself.

It matters more now than when it was written. The matched detector benchmark is not
runnable — no published checkpoint accepts input at the distances in question — so the
**comparison document is the deliverable**. Whether an outsider reads it correctly is
the product, not a box to tick.

Budget **30 minutes** with the reader, plus 30 minutes to write up.

---

## Who

Anyone **outside the GOOSE pair** — Kelsey, Aiden or Fatima. Not Ricky, who co-authored
the mapping and the statistics.

Fariya is the named reviewer for DZ-S3-1. If she also runs the read, note that she has
seen the document in review, which weakens it. A genuinely cold reader is better.

---

## The rule that makes this worth doing

**Say nothing while they read.** No framing, no "so what this shows is", no correcting a
misreading as it happens. The whole value is in what the artefact communicates without
you standing next to it — and you will not be standing next to it when the client or the
next team reads it.

**A misread is the finding, not a failure of the reader.** If they reach a wrong
conclusion, the document caused it. Write down what they said and fix the document.

Record answers **verbatim**. Do not tidy the grammar or summarise the gist — a hedge or
a hesitation is data.

---

## Materials

| Order | Artefact | Tests |
|---|---|---|
| 1 | `docs/evidence/goose_client_figure.png` alone, no caption | P-6 — key finding without narration |
| 2 | `docs/dataset-suitability.md` §5 and §7 | DS-4 — what each dataset can and cannot answer |

---

## Part 1 — the figure, no caption (10 min)

Show the image. Nothing else. Then ask, in this order:

1. **What do you think you are looking at?**
2. **What is it measuring?**
3. **Is anything in this picture produced by a model?**
4. **If a truck drove through this scene, does this picture tell you where it could
   safely go?**

Questions 3 and 4 are the ones that matter. They target the specific misreading this
figure is most likely to produce: that the traversability colouring is a model's
prediction of a safe route, when it is a **grouping of existing human labels**. If the
reader says "the model decided this" or "green means safe to drive", **that is a
documented P-6 failure** and the caption or figure has to change.

5. **What would you need to know before trusting it?**

---

## Part 2 — the comparison document (20 min)

Give them §5 and §7. Then:

6. **For each of the three datasets — what question can it answer?**
7. **Point at any number here. What is it a number *of*?**

Question 7 tests the denominator rule the whole document is built on. If they cannot say
what a figure covers, the inline denominators are not working.

8. **§5 shows LiDAR at 80.36% and radar at 37.50% at 200–400 m. What does that tell you
   about radar?**

This is the highest-risk sentence in the project right now. The correct reading is
*geometric support on five TruckDrive clips — an annotated vehicle box containing at
least one return — and not detection accuracy, not a general property of radar.* If the
reader concludes "radar is worse than LiDAR" without qualification, the caveats are not
doing their job, and that is exactly the overstatement this team has spent the semester
correcting in each other.

9. **Is there anything here you think is overstated?**
10. **What is still unknown?**

---

## Recording

Copy into `docs/evidence/p6-cold-read-<date>.md`, commit it, and link it from the
acceptance tests. **Unedited.**

```markdown
# P-6 / DS-4 cold read — <date>

Reader: <name> · Pair: <which dataset pair they worked on>
Prior exposure to these artefacts: <none / describe>
Run by: Damien Zhang
Narration given: <should be "none" — if any, say exactly what>

## Part 1 — figure without caption
Q1 what are you looking at:
Q2 what is it measuring:
Q3 is anything model-produced:        <-- P-6 critical
Q4 does it show where a truck could safely go:   <-- P-6 critical
Q5 what would you need before trusting it:

## Part 2 — comparison document
Q6 what can each dataset answer:
Q7 pick a number, what is it of:
Q8 what does 80.36% vs 37.50% tell you about radar:   <-- highest-risk
Q9 anything overstated:
Q10 what is still unknown:

## Outcome
P-6 (key finding without narration): met / not met — why
DS-4 (can and cannot answer):        met / not met — why

## Changes made as a result
<Each fix, with the commit. If none, say so and justify it.>
```

---

## How to report it

If they read it correctly, say precisely that: **one reader outside the pair, on these
two artefacts, on this date.** It is not proof the whole repository is readable.

If they misread it, the honest sequence is: record the misreading, change the artefact,
and note that **the fix is untested** — a second cold read with a different reader is
what would test it, and there may not be time. Saying so is better than implying the
fix worked.

Either way this closes the criterion by *performing* it. An unperformed test recorded as
"partly met" for a whole semester is worse than a failed one recorded honestly.
