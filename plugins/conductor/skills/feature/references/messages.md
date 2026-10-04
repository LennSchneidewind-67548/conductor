# Message templates

Plain, short, scannable. Write the user-facing text yourself; these are shapes, not fill-in forms.

## Progress (no stop; at most one line per event)
```
P1 part A merged (#24) · part B building
```

## Interview write-up (end of the interview stop)
```
Here's what I'm building:
You said
- …
I assume
- … (say if wrong)
Size: feature, 3 phases likely. Planning now.
```

## Decision (stop)
Ask through `AskUserQuestion`. Above it, at most 2 lines:
```
Decision needed (<Feature> P2 part B, paused; nothing else blocked)
<one sentence of context>
```

## Pick (stop)
```
Pick needed: <n> visual decisions, variants on <page link>
```
Then one `AskUserQuestion` question per decision, options named after the variants on the page.

## Review (stop)
```
Review ready: build <N> is in <where the review build puts it>
Install it, then check:
  • <check from the phase's Verification / Local checks>
  • <check>
Reply "ok" to close P<n>, or describe what's off.
```

## Sign-off (stop)
```
<Feature> is built: <n> phases, PRs #a–#b.
Deviations: <count, the 1–3 notable ones>
Docs updated: <files>
Retro: design/<feature>/RETRO.md (conductor improvements: <n>)
Say "done" to close the feature.
```
