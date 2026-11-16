# Brief template (fill every section; delete the hints)

**Role:** <role name from roles/*.md>  ·  **Stage:** <Discover | Define | Design | Build | Integrate | Verify | Accept | Release | Launch>

## Goal
<One paragraph: what to produce and why the owner wants it. Include the owner's own example if there is one.>

## Where
- Repo `<abs path>`, worktree `<abs path>` on branch `<branch>` (create: `git -C <repo> worktree add <path> -b <branch> <base>`), base `<commit>`.
- Read first: `<PRD/spec>`, `<contract>`, `<style guide>`, `<backlog>`, `<entry points>`.
- Files you own: <list/glob>. Files others own: <list>. Need a change there? Say so in your report.

## Decisions already made
- Owner: <…>
- Lead: <…>
- Defaults you may pick (list them back as "to confirm"): <…>

## Role card
<Paste Mission, Outputs, Checklist and Done-when from the role card.>

## Hard rules
- Never touch: <prod stack, other repos, live data, secrets, unlicensed sources>.
- No push / tag / deploy / publish / external messages <unless: …>.
- Commit identity `<name> <noreply email>` via `git -c user.name=… -c user.email=…`; message ends with: <trailer lines>.
- Host quirks: <toolchain wrappers, port range, GPU use>.
- Independence (QA/QC/security/reviewers): you get no builder conclusions; try to refute.

## Deliverables
1. <…>
2. <…>

## Done when
- <exact lint/type/test/build commands> pass (report counts)
- <e2e / screenshots: widths × themes → `<abs dir>`; open every one and fix what's wrong>
- Stop every server/container you started; keep only <final artifacts>.

## Return (plain language, no fluff)
Commits (sha + one line) · check results with numbers · what was NOT verified and why · decisions to revisit · defaults to confirm · best evidence (absolute paths/links) · open questions · cleanup done.
