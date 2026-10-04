# Ledger and retro formats

## `.conductor/ledger.md`
Git-ignored, coordinator-only. Overwrite the header fields and append to the log. Keep it short; it's read on every resume.

```markdown
# conductor ledger — feature: <slug>
Size: spike | bounded | feature
Plan: design/<slug>/PLAN.md
Stage: interview | feature-plan | picks | P<n> plan | P<n> part <X> | P<n> review | signoff | done
Started: <YYYY-MM-DD>

## Decisions asked (pointer; the full text is in PLAN.md Decisions)
- <short> → <answer>

## Rulings (by the coordinator)
- Ruling: <what> — <why> — <cost if wrong>

## Log
- <YYYY-MM-DD HH:MM> PLAN merged #12
- <…> P1 plan merged #13
- <…> P1 part A implementer <agent-id> on conductor/<slug>-p1-a → PR #14
- <…> P1 part A review CHANGES (round 1)
- <…> P1 part A merged #14
- <…> P1 review build 87 sent
- <…> P1 reviewed ok
```

Resume rule: the last log line plus `Stage` say what to do next. A part with a PR but no "merged" line is in review: check its state with `gh pr view <n>` before doing anything.

## `design/<feature>/RETRO.md`
Written at sign-off, committed. It's the feedback loop for improving conductor itself.

```markdown
# <Feature> retro

- **Shipped:** <phases and parts, with PR numbers>
- **Stops:** interview <n rounds> · picks <n> · decisions <n> · reviews <n>, each with one line on what it was
- **Rulings that held / that were wrong:** …
- **Where it stalled:** blocked workers, fix rounds that hit the cap, resumes after /clear
- **Usage:** <from /usage if available: coordinator vs subagent share>
- **Improve conductor:** concrete changes to a skill or agent prompt, 0–5 bullets
```
