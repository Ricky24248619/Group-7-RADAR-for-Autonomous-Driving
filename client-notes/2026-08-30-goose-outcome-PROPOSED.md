> ## ⚠️ For Ricky — read this, then delete this whole block if you adopt the note
>
> **This is a proposal, not a replacement.** `client-notes/` is yours under
> `WORKPLAN.md` §6 and RY-4 is your story, so I have not touched
> `2026-08-offroad-strand-update-DRAFT.md`. Take this, take parts of it, or bin it.
>
> ### Why I drafted it
>
> Your draft carries the instruction *"Hold until Damien's survey branch is merged and
> reviewed."* That merged on 28 August, so the hold is released — but four things have
> changed since you wrote it and it can't go as-is:
>
> | Your draft says | Now |
> |---|---|
> | "STONE parked on storage" | STONE was **dropped** at the 29 Aug meeting |
> | Recommendation 1 asks for ~645 GB for STONE | Moot — and it was the biggest, most stallable ask in the note |
> | ROS 1 vs ROS 2 "unconfirmed" | **ROS 1**, stated by the paper's first author in issue #18 |
> | Radar "unlabelled" | Also **unobtainable** — released bags carry a reduced sensor set |
>
> ### The structural change, which matters more than the corrections
>
> Your draft is organised around **STONE** as the headline with GOOSE supporting. That
> was right a week ago. It is now backwards: GOOSE is the thing that worked, STONE is a
> closed question, and the note should lead with the result rather than the blocker.
>
> I also cut it to **one ask**. Yours had three plus a "meanwhile". Adrian has not
> replied in two and a half weeks; a note with three questions gives him three reasons
> to defer. Kaya is the only one that blocks us, so it is the only one in the body —
> the other two are a footnote he can ignore without cost.
>
> ### What this means for your work
>
> - **RY-4 is satisfied either way** — by this or by your own revision. The four-part
>   structure and the two-minute target are unchanged; only the content moved.
> - **It makes the case for DZ-3's failure rule.** The strongest paragraph in this note
>   is the one saying we could not run the model. A year from now that is the paragraph
>   the auditor reads. Worth remembering when you write up R7 — whichever way it goes,
>   it becomes the next client note.
> - **It sets a cadence.** One note per real outcome, not per sprint. R7 produces the
>   next one.
> - **It does not depend on R6.** Your two loose ends (third experiment-log entry, the
>   projection caveat in `metrics-definitions.md`) are unrelated to this and still open.
>
> ### Before sending
>
> The figure has not had a cold read by anyone outside our pair, which is D4's own
> acceptance test. Ask Kelsey or Fatima what they think it shows **before** this goes
> to Adrian. If it needs narrating, it is not ready.

---

**From:** Team 07 · **To:** Adrian Boeing, Fabian · **Date:** 30 August 2026
**Re:** GOOSE works — and the one thing we need from you

## What we tested

Whether GOOSE — the off-road dataset you asked us to keep — can answer the question you
set at kickoff: *what can I drive over, what can I crash into?* And whether we can run
an existing open-source model on it.

## What happened

**GOOSE works.** Two of us installed it independently, on macOS and Windows, and both
reproduced the same result from a clean machine. We measured the full validation split —
961 frames, 174.9 million hand-labelled points — and built a four-class map over its 64
surface types: drivable, uncertain, blocked.

![What the vehicle can drive on](../docs/evidence/goose_client_figure.png)

**Three findings that change our planning:**

1. **GOOSE cannot answer the long-range question.** 62.9% of its labelled points fall
   within 25 m and only 3.8% beyond 100 m. Almost no data at the distances a truck
   needs. Long range stays with TruckDrive.
2. **GOOSE's radar is not obtainable.** The vehicle carries six radars, but they are
   unlabelled and absent from the download — the authors confirm the released raw files
   carry only a reduced sensor set.
3. **We could not run the published baseline model.** It ships only as a CUDA image;
   our machines are Apple Silicon and one laptop with a 6 GB GPU. We established that in
   fifteen minutes by checking prerequisites rather than losing a day to a build that
   could not succeed.

## What it means

The **terrain half** of your off-road interest is answerable now, on the dataset you
asked us to keep.

The **radar half** is not answerable on GOOSE. It needed STONE — the one off-road
dataset with annotated 4D radar — and we have dropped it: a single 346 GB download, no
toolkit in its repository, and maintainers who have not answered a question since March.

We have reached the limit of what our laptops can do. The next step is running models,
and that needs compute.

## What we need

**The Kaya application. It is the only thing blocking us.**

You agreed to act as our Principal Investigator — the part we could not supply
ourselves. Thank you. The application also needs a data management plan, ORCIDs for all
six of us, a linked GitHub repository and an IRDS storage share. The repository exists
and the ORCIDs are ours to sort.

**Could we book twenty minutes with you to finish the rest?** It is the difference
between reporting what these datasets contain and reporting how models perform on them.

---

*Two smaller things, no rush.* **Fabian:** we have assigned all 64 GOOSE surface classes
to four traversability levels and would value a sanity check; the reasoning is written
down per class. **Adrian:** we are still waiting on a reply about the auditor meeting.

*All of the above is documented with evidence in our repository — surveys, measurements,
and a record of what worked and what did not.*
