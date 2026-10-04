# conductor v1: one coordinator session per feature

## Context
Right now, about half of the work on personal projects goes into session admin: starting and clearing sessions, prompting for plans, prompting to implement, asking "is this phase done?", and merging. The research (artifact "One session, many agents") compared options and you chose **option A**: our own Claude Code plugin built from native features, with ideas borrowed from Superpowers, GSD Core and Compound Engineering. It lives in a **new public repo `conductor`**, every change still goes through **PRs**, and there is **one coordinator session per feature**. The pilot feature gets picked after it's built.

Target experience: open `claude` in a project and run `/conductor:feature <idea>`. Claude interviews you, and from then on you only hear from it at four typed stops: **interview**, **pick** (visual variants), **decision** (something only you can settle), and **review** (build on the iPhone), plus a final **sign-off**. Everything else runs on its own: phase plans, implementation, review, PRs, merges, and plan/doc updates.

It codifies the process fuel already uses by hand (`design/collection/P0c.md`):
- `design/<feature>/PLAN.md` holds the feature, and `P<n>.md` files hold the phases.
- A phase splits into **parts**, built one at a time, with one PR per part.
- The commit style is `<Feature> <Phase> step N: …`.
- A "Deviations found while building …" section records changes from the plan.
- Local checks are listed in the PR body.

## What we borrow, and from where
| Idea | Source | How conductor uses it |
|---|---|---|
| Sort the request by size before asking | Superpowers brainstorming (spike / bounded / architectural) | The interview depth and plan weight scale with size. A bounded change gets no PLAN.md |
| Write back what you understood, split into "you said" and "I assume" | Superpowers brainstorming | Ends every interview |
| Gray areas → locked decisions | GSD discuss-phase | PLAN.md gets a "Decisions" list that later agents may not reopen |
| Fresh subagent per unit plus a status contract `DONE / DONE_WITH_CONCERNS / NEEDS_DECISION / BLOCKED` | Superpowers SDD | Every worker report ends with it |
| Deviation rules 1–3 (bug, missing correctness, blocker → fix and log) vs rule 4 (structural → stop and ask). Never install a package without asking | GSD executor | Implementer rules |
| "Rulings, not stalls": decide, log `Ruling: what — why — cost if wrong`, keep going | Superpowers SDD | Anything that doesn't change what you'd see or feel gets ruled, not asked |
| An on-disk ledger is the source of truth after compaction; never redo work it lists as done | Superpowers SDD | `.conductor/ledger.md` |
| Model per role, and a cap on fix rounds | Superpowers SDD | Opus plans, Sonnet builds and reviews. At most 2 fix rounds, then decide or escalate |
| Capture lessons only if they would otherwise be lost | Compound Engineering ce-compound | Retro at sign-off: CLAUDE.md/SPEC.md updates + `RETRO.md` + ideas for improving conductor |

What we deliberately leave out: mandatory TDD, a review agent for every task, persona agents, approval gates between phases, parallel streams.

## Repo layout (`~/Developer/conductor`, public, MIT)
```
.claude-plugin/marketplace.json      lists ./plugins/conductor
plugins/conductor/
  .claude-plugin/plugin.json
  skills/feature/SKILL.md            coordinator (user-invoked only)
  skills/feature/references/         loaded on demand: ledger.md, escalation.md, messages.md (phase shape lives in planner.md)
  skills/status/SKILL.md             where are we, what's waiting on me
  skills/setup/SKILL.md              adds a "## Pipeline" section to a project's CLAUDE.md
  agents/planner.md                  opus, high effort
  agents/implementer.md              sonnet, isolation: worktree
  agents/reviewer.md                 sonnet (coordinator may pass opus for big diffs)
design/v1/PLAN.md                    this plan (repo convention)
README.md                            what it is, the flow, design rationale + credits (portfolio-facing)
```
Plugin agents can't set `hooks`, `mcpServers` or `permissionMode` (docs). That's fine: they inherit the session's auto mode.

## The coordinator loop (`skills/feature/SKILL.md`)
1. **Start or resume.** If `.conductor/ledger.md` exists (git-ignored), read it and `git log`, then continue at the first unfinished step. Otherwise read the project's CLAUDE.md `## Pipeline` section (or tell you to run `/conductor:setup`).
2. **Interview** <sub>(stop: interview)</sub>
   - Classify the request first: spike, bounded or feature.
   - Ask in rounds with `AskUserQuestion`. Each option is a concrete choice, and the recommended one comes first.
   - Write back the understanding, split into "you said" and "I assume".
3. **Feature plan.** Write `design/<feature>/PLAN.md`: Context, Decisions (locked), Architecture, Phases. For a **feature**, the planner subagent drafts it and the coordinator posts a 5-line summary. That's not an approval gate: you can object, but it continues.
4. **Picks** <sub>(stop: pick)</sub>. Only when the plan has open visual decisions. The coordinator publishes a gallery page of variants (artifact) and you choose. The choices go into Decisions.
5. **Per phase:**
   - The planner writes `P<n>.md`, shaped like `P0c.md`: Context, Steps, Docs, Verification, Parts table, Local checks. It returns open questions, already split into "ruled" and "needs you".
   - **Per part, in sequence:**
     1. Implementer runs in a worktree on a branch `conductor/<feature>-<phase>-<part>`. It commits per step, runs the Pipeline verify command, pushes, and opens a PR whose body lists the local checks.
     2. Reviewer reviews the PR diff against `P<n>.md` and CLAUDE.md rules.
     3. Up to 2 fix rounds go through `SendMessage` to the same implementer.
     4. Green: `gh pr merge --merge --delete-branch`, remove the worktree, append to the ledger.
   - `NEEDS_DECISION` <sub>(stop: decision)</sub>: the coordinator asks you one compact `AskUserQuestion` with its default, then resumes the worker.
6. **Review** <sub>(stop: review)</sub>
   - After each phase, or when a phase says it needs the device, run the Pipeline review build (fuel: `npm run ios:ipa` → iCloud).
   - Send a message: "build N is in iCloud. Check: …" with the phase's local and device checks.
   - "ok" closes the phase. Anything else becomes a fix part.
7. **Sign-off** <sub>(stop: sign-off)</sub>
   - The planner proposes the SPEC.md and CLAUDE.md updates the plan deferred; they go out as a final docs PR.
   - Write `design/<feature>/RETRO.md`: what stalled, what it asked you, rulings, and conductor improvements.
   - Delete the ledger. You say done.

Context discipline: the coordinator reads only plan docs, the ledger and worker reports, never source files or logs. Workers return about 300 words or less. Message templates (decision / review / progress) live in `references/messages.md`, worded like the examples on the research page.

## Agent contracts (shared, in each agent file)
- **Input:** the paths to read (CLAUDE.md is auto-loaded; PLAN.md, P<n>.md, the part name) plus the locked Decisions. No conversation history.
- **Output:** a summary, commits, a PR URL, deviations logged in PLAN.md's Deviations section, rulings, and then `Status:` with one of the four values.
- **Implementer:**
  - Builds only its part's steps.
  - Follows GSD rules 1–4; no new dependencies without `NEEDS_DECISION`.
  - Ends with the Pipeline verify command green, or `BLOCKED` with the output.
- **Reviewer:**
  - Read-only (`tools`: Read, Grep, Glob, Bash for `gh pr diff` and tests).
  - Looks for spec compliance first, then project rules and correctness.
  - Findings are `must-fix` or `note`. Only must-fix triggers a fix round.

## Per-project config: `## Pipeline` in CLAUDE.md (written by `/conductor:setup`)
For fuel:
- verify: `npm run lint && npm test && npm run build`
- review build: `npm run ios:ipa`, which puts the .ipa in iCloud for SideStore
- plans: `design/<feature>/`, phases `P<n>.md`
- commit style: `<Feature> <Phase> step N: …`
- part rules (from P0c): don't touch `ios/`; leave haptic `tuning` alone; no new deps.
- visual decisions: anything you see or feel (layout, motion, haptics, copy) → pick or decision; everything else → ruling.

Setup also adds `.conductor/` to `.gitignore`.

## Build order (this session, I write the files directly)
1. Scaffold `~/Developer/conductor`: git init, README, LICENSE, marketplace.json, plugin.json. Run `claude plugin validate .`, then `gh repo create conductor --public --source . --push`. Copy this plan to `design/v1/PLAN.md`.
2. Agents: planner, implementer, reviewer.
3. Skills: feature (+ references), status, setup.
4. Install at user scope: `claude plugin marketplace add ~/Developer/conductor`, then `claude plugin install conductor@conductor`, so every project has it. Updates come from `git pull` plus `claude plugin marketplace update`.
5. fuel: run `/conductor:setup`, then open a PR to fuel with the CLAUDE.md Pipeline section and `.gitignore`.
6. Dry run (below). Fix what it shows and commit to conductor via PR, starting there as it means to go on.

## Verification
- `claude plugin validate ~/Developer/conductor` passes. In a new session, `/conductor:feature`, `/conductor:status` and `/conductor:setup` are listed, and the three agents appear in `/agents`.
- **Dry run end-to-end** in a throwaway public repo `conductor-sandbox` (a tiny Vite app with a test). It gets a bounded request and a 2-part feature. Check that:
  - the interview uses multiple-choice rounds and writes back what it understood
  - PLAN.md and P1.md match the fuel shape
  - each part gets a worktree, a branch, a PR, a reviewer pass, and a merge with no prompt from me in between
  - a planted ambiguity comes back as exactly one decision question, and the worker resumes after it
  - `/clear` mid-feature, then `/conductor:feature` again, resumes from the ledger without redoing merged parts
  - the review stop runs the sandbox's review command and sends the checklist message
  - the retro gets written
- `/usage` after the dry run: the coordinator's context stays small (worker output doesn't flood it). Note the totals in RETRO.md as the token baseline.
- The pilot on fuel comes later, when you pick a feature.
