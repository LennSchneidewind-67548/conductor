---
name: break
description: Pause the current conductor feature at the next safe point so the session can be closed and resumed later in a fresh one, e.g. to save usage for other work. Starts nothing new, lets a running worker return, checkpoints the ledger.
disable-model-invocation: true
---

# conductor: break

The user wants to stop spending on this feature and close the session safely. Bring the feature to the nearest point where nothing lives only in this session's context, then say so. Don't finish more work than that: the point of a break is to save usage.

## 1. Mark the pause
Read `.conductor/ledger.md`. If it doesn't exist, say no feature is in progress and the session can be closed.

Otherwise set `Paused: requested <YYYY-MM-DD HH:MM>` in the ledger header right away, before anything else, and post one line: `Pausing after <what's running>. Starting nothing new.`

From now on, don't spawn a new worker, don't send a worker a new task, and don't run a review build.

## 2. Let the running worker return
If a worker you spawned in this session is still running, don't stop it: its tokens are already spent, and killing it loses its context and leaves its worktree half-built. End your turn and wait for its report. Then handle the report only up to the safe point below:

| Report | Do this, then stop |
|---|---|
| implementer `DONE` / `DONE_WITH_CONCERNS` | Log the PR. Don't spawn the reviewer. Pending: `review P<n> part <X> (#<pr>)`, with any concerns it named. |
| implementer `NEEDS_DECISION` | Log the question and its default. Don't ask it now. Pending: `ask: <question> (default: <x>)`. |
| implementer `BLOCKED` | Log the reason. Pending: `unblock P<n> part <X>: <reason>`. |
| reviewer `CHANGES` | Post the must-fix list as a PR comment and log the round, exactly as in the feature skill step 5.4. Don't send it to the implementer. Pending: `fix round <r> on #<pr>`. |
| reviewer `APPROVE` | Merge and log it as in the feature skill step 5.5 (it's cheap and leaves the tree clean). Pending: the next part. |
| planner `DONE` | Merge its PR and log it as the feature skill says for that mode. Pending: its "Needs you" items, or the next step. |

If no worker is running (you're at a stop waiting on the user, or between steps), there's nothing to wait for. If a question was open (`AskUserQuestion` not yet answered), log it as pending.

If this session didn't spawn the running work (e.g. `/conductor:break` in a fresh session), you can't wait on it: check `git worktree list` and `gh pr list --search "head:conductor/" --limit 5`, log what you see, and continue at step 3.

## 3. Checkpoint
1. Make sure the main checkout is on the default branch with nothing uncommitted. Remove an implementer worktree only if it's clean and its branch is pushed (`git -C <path> status --short` empty, nothing in `git -C <path> log @{u}..`); leave any other one, since it holds work that isn't on GitHub yet.
2. Update the ledger: `Stage` is the step that resumes, `Paused: <YYYY-MM-DD HH:MM> · next: <pending>`, and a log line `- <time> paused · next: <pending>`.
3. Send this and stop:
   ```
   <Feature> paused at <Stage>. Ledger is up to date; nothing is lost.
   Next on resume: <pending>
   Safe to close. Later, in a fresh session: /conductor:feature
   ```
