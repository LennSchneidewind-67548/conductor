---
name: setup
description: Prepare a project for conductor by adding a "## Pipeline" section to its CLAUDE.md (verify command, review build, plan location, commit style, part rules) and git-ignoring .conductor/.
disable-model-invocation: true
---

# conductor: setup

Write the project's `## Pipeline` section, the config every conductor agent reads. Propose it, let the user correct it, then write it.

## 1. Gather (read-only)
- Package scripts (`package.json`, `Makefile`, `pyproject.toml`, `Cargo.toml`, …): lint, typecheck, test, build.
- CI config (`.github/workflows/`), if any: it shows what "green" means here.
- An existing plan convention (`design/`, `docs/plans/`, `specs/`): look at one or two plan files to get their shape and how phases are named.
- `git log --oneline -30`: the commit-message style.
- CLAUDE.md and README: rules agents must follow, and how the user looks at a build (dev server, device, deploy preview).
- The default branch, and whether `gh` is authenticated (`gh auth status`).

## 2. Propose
Show the draft, then ask about anything you couldn't infer in one `AskUserQuestion` call (usually: the review build, and what counts as a visual decision).

```markdown
## Pipeline
Used by the conductor plugin (`/conductor:feature`).
- **Verify** (must pass before a PR): `<cmd && cmd && cmd>`
- **Review build** (for the user's look): `<cmd>` → <where the result lands and how the user opens it>
- **Screenshot** (web projects, optional): `<cmd that saves a PNG of the built page, e.g. headless Chrome against the preview server>`
- **Review after:** each phase | phases with device or browser checks
- **Plans:** `<dir>/<feature>/PLAN.md`, phases `P<n>.md`, shaped like `<example path>`
- **Commits:** `<style, e.g. "<Feature> P<n> step N: …">`
- **Part rules:** <files or areas a part must not touch; no new dependencies; other hard rules>
- **Visual decisions:** <what counts as see-or-feel in this project> → ask; everything else → rule
```

Keep the existing CLAUDE.md as it is. Add the section at the end.

## 3. Write
On the user's OK:
1. Add the section to CLAUDE.md.
2. Add `.conductor/` to `.gitignore`.
3. Commit on branch `conductor/setup` (`Add conductor pipeline config`), push, and open a PR.
4. Merge it if the user's earlier answers already approved the content; otherwise leave the link.

Finish with one line: "Ready. Start a feature with `/conductor:feature <idea>`."
