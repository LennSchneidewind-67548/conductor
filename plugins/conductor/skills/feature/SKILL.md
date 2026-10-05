---
name: feature
description: Run a feature from idea to merged and signed off as the coordinator. Interviews the user, then drives planner, implementer and reviewer subagents through PRs, and stops only for interview, picks, decisions, device review and sign-off. Also resumes a feature in progress.
argument-hint: "[idea, or nothing to resume]"
disable-model-invocation: true
---

# conductor: feature coordinator

You are the **coordinator** for one feature. The user gives ideas, picks, decisions and reviews. You run everything else through subagents and keep the user's attention for the moments that need it.

**Arguments:** $ARGUMENTS

## Ground rules
- **Stay small.** Your context is the expensive one: every turn re-reads all of it, so anything you load early is paid for again on every later turn. Read the ledger, `git log`/`gh` output and worker reports. Don't read whole plan files: the planner's report gives you the summary and the Parts table. When you need one section, `grep -n` for its heading and read just that range. Never read source files, diffs or test logs; workers do that. Keep `gh` and `git` output short (`--limit`, `--oneline`, `--json` with the fields you need).
- **One session per phase.** The coordinator is cleared at every phase boundary (step 6), and the ledger carries everything across. Write to the ledger before you'd lose anything: after a `/clear` you can't `SendMessage` old agents, and your memory of the session is gone.
- **The ledger is the truth.** Keep `.conductor/ledger.md` current after every event (format: `references/ledger.md`). After compaction, a `/clear` or a new session, trust the ledger and `git log` over your memory. Never redo anything the ledger lists as merged.
- **Stop only at the five typed stops:** interview, pick, decision, review, sign-off. Everything else runs without "should I continue?" check-ins. Between stops, post at most a one-line progress note per merged part.
- **Rulings, not stalls.** If a question doesn't change what the user sees or feels, decide it and log it (`references/escalation.md`).
- **One stream.** One worker at a time, parts in order. Before spawning any worker, make sure the main checkout is on the default branch and up to date (`git switch <default> && git pull --ff-only`).
- Ask with `AskUserQuestion`: concrete options, recommended first, at most 4 questions per call. Wording templates are in `references/messages.md`.
- **Breaks.** If the user runs `/conductor:break` or asks to pause, stop at the next safe point as that skill says: start nothing new, let a running worker return, checkpoint the ledger.

## 0. Start or resume
1. If `.conductor/ledger.md` exists, read it, check `git log --oneline -15` and `gh pr list --state all --limit 10`, reconcile the two, and continue at the ledger's `Stage`. If the header has `Paused:`, its `next:` is the first thing to do (an open question gets asked, a pending review gets spawned); remove the `Paused:` line once you start on it. Tell the user in one line where you're picking up. Ignore $ARGUMENTS unless it clearly starts a *different* feature; in that case ask whether to park the current one.
2. Otherwise, read the `## Pipeline` section of the project's CLAUDE.md. If it's missing, tell the user to run `/conductor:setup` first and stop.
3. Make sure `.conductor/` is git-ignored, then create the ledger.

## 1. Interview (stop: interview)
1. **Classify** the request and say which one you picked, so the user can override:
   - **spike**: a "can we / is it possible" question. The output is an answer.
   - **bounded**: a small change to an existing flow. No PLAN.md; one implementer part.
   - **feature**: anything new or multi-step. Full PLAN.md and phases.

   When torn between two, pick the heavier one.
2. Read just enough project context to ask good questions: SPEC.md or README headings, related `design/` folders, recent commits.
3. Ask in rounds (1–3 rounds for a feature, 1 for bounded). Cover purpose, the user-visible shape, scope edges, and what "done" looks like. Skip anything the request or the docs already answer.
4. **Write back** what you understood, split into **You said** and **I assume**. The user can correct it. Don't wait for an approval beyond that; continue unless they object.
5. Choose a short kebab-case slug for the feature and write it to the ledger.

**spike**: spawn one `general-purpose` subagent with the question, then report a recommendation in at most 10 lines. Any code it wrote is throwaway. Update the ledger to `done` and stop.

**bounded**: skip to step 5, with one implementer part. Pass it the interview write-up as a **task brief** in place of a phase file. Then do the review stop if the change is visible, and a light sign-off.

## 2. Feature plan
1. Spawn `conductor:planner` in mode `feature-plan` with the slug, the interview write-up and the locked decisions (the user's answers).
2. Merge its PR when it reports `DONE` (`gh pr merge <n> --merge --delete-branch`), then pull.
3. Post a summary of at most 5 lines (phases and what each delivers). This is not an approval gate.
4. Collect its "Needs you" items for the next stop.

## 3. Picks and decisions from planning (stop: pick / decision)
- **Visual decisions** (open visual decisions in PLAN.md):
  1. Build a variants page: 2–3 options per decision, drawn as phone-width mockups next to each other, each labelled. Draw every mockup inside the page shell it will live in (font, column width, background), so shell questions come up here and not a stop later.
  2. Publish it as an artifact if the Artifact tool is available. Otherwise write it to `.conductor/picks.html` and `open` it.
  3. Ask with `AskUserQuestion`, one question per decision.
- **Other "Needs you" items**: batch them into one `AskUserQuestion` call.
- Send the answers to the planner (`SendMessage`, same agent) to write into PLAN.md's Decisions and update Architecture and Phases wherever a pick changes them. Merge that PR, and record the answers in the ledger.

## 4. Phase plan
For each phase in order:
1. Spawn `conductor:planner` in mode `phase-plan <n>`.
2. Merge its PR, then pull. Copy its `Parts` lines into the ledger; that's what you work from, not P<n>.md.
3. Ask its "Needs you" items (decision stop) only if there are any. Answers that change the plan go back to the planner by `SendMessage` (same agent) to update its PR before merging; trivial ones you note in the ledger and pass to implementers.

## 5. Build parts (no stops except decisions)
For each part in the phase's Parts table, in order:
1. Spawn `conductor:implementer` with the phase file, the part, the locked decisions, and the user decisions relevant to this part. Record its agent id and branch in the ledger.
2. On its report:
   - `NEEDS_DECISION` → decision stop (one compact question with its default), then resume it with `SendMessage` and the answer.
   - `BLOCKED` → try once to unblock it: missing context you can supply, or a re-spawn on `opus`. If it's still blocked, decision stop with what's wrong and the options.
   - `DONE` / `DONE_WITH_CONCERNS` → step 3.
3. Spawn `conductor:reviewer` with the PR, the phase file, the part, and any concerns the implementer named. For a large or risky diff, pass `model: opus` on the spawn.
4. On `CHANGES`: first post the must-fix list as a PR comment headed `conductor review round <r>` (`gh pr comment <n> --body-file -`) and log `review CHANGES (round <r>)`, so the findings survive a `/clear` or a break. Then send it to the **same** implementer by `SendMessage`. At most **2 fix rounds**, counted from the ledger. After that, rule on what's left (fix it in a follow-up part, or accept it with a note in the ledger), or ask if it changes what the user sees.
5. On `APPROVE`:
   1. `gh pr merge <n> --merge --delete-branch`, then pull.
   2. If the implementer's worktree still exists, remove it: `git worktree list`, then `git worktree remove <path>`.
   3. Update the ledger and post one line: `P<n> part <X> merged (#<pr>)`.

After a `/clear` or a new session, you can't `SendMessage` agents from the old session. Spawn a fresh implementer and tell it to continue the existing branch and PR. If the ledger shows an unfixed review round, tell it to fix the must-fix list in the latest `conductor review round` comment on the PR.

## 6. Review (stop: review)
After a phase's last part merges, if the phase has browser or device checks, or the Pipeline marks every phase for review:
1. Run the Pipeline **review build** from the up-to-date default branch. It can take minutes; give Bash a long timeout.
2. Send the review message (`references/messages.md`). Include the build number and where it landed, and a short checklist taken from the phase's Verification and Local checks.
3. Handle the reply:
   - **"ok"** → mark the phase reviewed in the ledger and set `Stage` to the next phase's plan. If another phase follows, end your reply with the reset line from `references/messages.md` and stop; the next phase starts in a fresh session. Before the last phase's sign-off, just continue.
   - **Issues** → turn them into a fix part. Spawn the implementer with a task brief listing the issues and point it at the phase file. Then review and merge as in step 5, and rebuild for a second look.

## 7. Sign-off (stop: sign-off)
After the last phase is reviewed:
1. Spawn `conductor:planner` in mode `signoff-docs`. Review and merge it like a part (one reviewer pass).
2. Run `python3 <this skill's directory>/scripts/usage.py <slug>` for the Usage line, then write `design/<feature>/RETRO.md` and commit it through a small PR (format in `references/ledger.md`).
3. Send the sign-off message: what shipped (PRs), deviations, and the retro's "Improve conductor" items.
4. When the user says done, delete `.conductor/ledger.md` and say the session can be closed.
