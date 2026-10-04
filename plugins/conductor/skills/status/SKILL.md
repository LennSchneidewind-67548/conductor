---
name: status
description: Show where the current conductor feature stands and what, if anything, is waiting on the user. Read-only.
disable-model-invocation: true
---

# conductor: status

Read `.conductor/ledger.md`. If it doesn't exist, say no feature is in progress and that `/conductor:feature <idea>` starts one.

Otherwise, check the open PRs on `conductor/*` branches (`gh pr list --search "head:conductor/"`), then answer in at most 8 lines:

```
<Feature> · <Stage>
Done: <phases/parts merged, with PR numbers>
Now: <what's running or paused>
Waiting on you: <the open decision/pick/review, or "nothing">
Next: <the step after this one>
```

Don't change anything. If this is a new session and the ledger shows work in progress, end with: "Run `/conductor:feature` to resume."
