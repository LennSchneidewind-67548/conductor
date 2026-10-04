# Ask or rule?

The user wants to spend attention on ideas, look-and-feel and sign-off, nothing else. Every question you ask costs them a context switch. Every wrong ruling costs a fix part they can see and undo. Weigh the two.

## Ask the user (decision or pick stop) when it…
- changes what the user **sees or feels**: layout, motion, haptics, copy, colors, game balance, numbers shown
- contradicts a locked decision or the user's words in the interview
- adds a **dependency**, a data migration, or a permanent stored field or format
- is irreversible or reaches outside the repo: deleting data, force-pushing, publishing, spending money
- is a structural change (implementer rule 4) the plan didn't foresee
- leaves every path forward a guess

The project's `## Pipeline` "visual decisions" line can widen or narrow the first bullet.

## Rule yourself when it…
- is internal: naming, file layout, helper shapes, test structure, refactors inside the part's scope
- has an answer the code, CLAUDE.md, SPEC.md or earlier plans already point to
- is a bug, a missing check or a blocker (implementer rules 1–3)

Log every ruling as `Ruling: <what> — <why> — <cost if wrong>` in the ledger. Workers log theirs in PLAN.md Deviations.

## How to ask
- One `AskUserQuestion` call, batching everything that's waiting, at most 4 questions.
- Each question: one sentence of context, then 2–3 concrete options with the recommended one first, labelled "(Recommended)".
- Say what's paused and what keeps running, e.g. "P2 part B is paused; nothing else is blocked."
- Never ask "should I continue?", "is this plan ok?" or "can I merge?". The user already said yes to all of those by starting `/conductor:feature`.
