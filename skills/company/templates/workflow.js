// Company pipeline template: contract -> parallel builders -> integrator -> verifiers.
// Copy into the Workflow tool's `script` (plain JS), fill the CAPS parts. Load `workflow-authoring` first.
// Run only AFTER the customer approved the requirement set (requirements.md); give agents docs/requirements/*.
// Progress: call log() at every stage boundary; the Project coordinator reads the journal + git/CI to refresh the live progress page.
export const meta = {
  name: 'company-feature',
  description: 'Architect contract, parallel builder teams, integrator, safety + UI verifiers',
  phases: [
    { title: 'Contract', detail: 'architect fixes schemas, API stubs, interfaces, file ownership' },
    { title: 'Build', detail: 'builder teams in parallel worktrees' },
    { title: 'Integrate', detail: 'merge teams, glue, end-to-end example' },
    { title: 'Verify', detail: 'adversarial backend/safety + UI/e2e with screenshots' },
  ],
}

const REPO = 'ABS_REPO_PATH'
const WT = `${REPO}/.claude/worktrees`
const MAIN = 'feat/FEATURE'
const RULES = `
HARD RULES:
- Spec: ABS_SPEC_PATH (read fully). Work ONLY in your own worktree under ${WT}/. Never edit the main checkout.
- Never push, tag, deploy, or touch: PROD_STACK, OTHER_REPOS, LIVE_DATA.
- Host quirks: HOST_QUIRKS. Test servers only on 127.0.0.1 ports PORT_RANGE; stop them when done.
- Quality bar: LINT/TYPE/TEST COMMANDS; pinned deps; tests for every behaviour.
- Design/licence: DESIGN_RULES.
- Commit as: git -c user.name=NAME -c user.email=NOREPLY commit ... ending with:
TRAILER_LINES
`

phase('Contract')
const contract = await agent(`${RULES}
ROLE: ARCHITECT. Create the integration worktree: git -C ${REPO} worktree add ${WT}/main-int -b ${MAIN} HEAD
Write the contract the teams build against: models/schemas, API routes as 501 stubs with final request/response models,
message types, state names, a spec section "Implementation map" (module layout, file ownership per team, storage layout,
exact interfaces). Regenerate clients/types. All checks green. Commit.
Return: commit sha, file-ownership map per team, verbatim interface signatures.`,
  { label: 'architect', phase: 'Contract' })

const TEAMS = [
  { key: 'A', branch: 'feat/FEATURE-a', prompt: 'TEAM A - SLICE A: ...' },
  { key: 'B', branch: 'feat/FEATURE-b', prompt: 'TEAM B - SLICE B: ...' },
  { key: 'C', branch: 'feat/FEATURE-ui', prompt: 'TEAM C - UI: ... (build against stubs/mocks of the contract)' },
]

phase('Build')
const builds = await parallel(TEAMS.map(t => () => agent(`${RULES}
CONTRACT (from the architect):
${contract}

Create your worktree: git -C ${REPO} worktree add ${WT}/team-${t.key} -b ${t.branch} ${MAIN}
Edit ONLY the files your team owns per the map. ${t.prompt}
Run all checks, commit. Return: commits, check results, what is not done, interface changes you needed (should be none).`,
  { label: `team-${t.key}`, phase: 'Build' })))

phase('Integrate')
const integ = await agent(`${RULES}
ROLE: INTEGRATOR in ${WT}/main-int (branch ${MAIN}). Merge ${TEAMS.map(t => t.branch).join(', ')} (keep both sides on conflicts).
Team reports:
${builds.filter(Boolean).join('\n---\n')}
Write the glue (RUNTIME/WIRING), then an end-to-end test of the owner's example: OWNER_EXAMPLE.
All checks green. Commit. Return: commits, checks, decisions you made that the Lead may revisit.`,
  { label: 'integrator', phase: 'Integrate' })

phase('Verify')
const verify = await parallel([
  () => agent(`${RULES}
ROLE: SAFETY/BACKEND VERIFIER on ${WT}/main-int. Do not trust earlier reports; read the code and try to break it
(limits, races, malformed/huge input, auth, path traversal, SAFETY_SPECIFICS). Each real bug: separate commit + failing-first test.
Stage only your own files (a UI verifier commits in the same worktree). Return a PASS/FAIL table with evidence, commits, residual risks.`,
    { label: 'verify-safety', phase: 'Verify' }),
  () => agent(`${RULES}
ROLE: UI/E2E VERIFIER on ${WT}/main-int. Build the app, drive the owner's example with Playwright using only the mouse,
screenshots 1280/390 x light/dark into SHOTS_DIR, look at every one, fix UI bugs in small commits with tests (frontend files only).
Return: steps run, best 8 screenshots (absolute paths), fixes (sha + one line), remaining issues.`,
    { label: 'verify-ui', phase: 'Verify' }),
])

return { contract, builds, integ, verify }
