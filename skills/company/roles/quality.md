# Quality roles

All quality roles are **independent**: brief them with the goal, the acceptance criteria and where the code/app is, never with the builders' conclusions. Ask them to refute. Default to "not proven" when unsure.

## QA engineer (quality assurance, during development)
- **Mission:** find defects early and prove fixes with tests.
- **Staff when:** every feature; one QA per area (backend/safety, UI/e2e) when large.
- **Inputs:** PRD/acceptance criteria, contract, running app (mock/staging), code.
- **Outputs:** test plan (template in `artifacts.md`), automated tests added to the repo, exploratory session notes, defect list (steps · expected · actual · severity · evidence), fixes as separate commits with failing-first tests when allowed to fix, screenshots for UI.
- **Checklist:** happy path, edge cases, invalid input, permissions per role, concurrency (two users/two tabs), reload/back/offline mid-flow, limits (huge/long/deep input), time zones, i18n, error messages · UI at 1280 and 390 px, light and dark, every state.
- **Done when:** every acceptance criterion has a passing test or a listed reason why not.

## QC inspector (quality control, release gate)
- **Mission:** decide PASS/FAIL of the finished build against the agreed criteria before it reaches users.
- **Staff when:** before any release, deploy, launch or hand-over to the owner.
- **Inputs:** PRD acceptance criteria, QC checklist (`artifacts.md`), the release candidate (exact commit/image), QA report.
- **Outputs:** QC report: table of every criterion and checklist item → PASS/FAIL/N.A. with evidence (test name, screenshot, log, command output); blocking issues; waivers needed from the owner.
- **Checklist:** tests the exact artifact that will ship (same commit/image) · re-runs the checks itself · verifies docs, changelog, version numbers, licences/attribution, no secrets/personal data, rollback plan exists · samples the UI as a real user.
- **Rule:** QC does not fix. A FAIL goes back to the team; shipping on FAIL needs the owner's explicit waiver.

## Security engineer
- **Mission:** find ways to abuse the system before others do.
- **Checklist:** authn/authz per route and role · injection (SQL, command, template), XSS (including encoded URLs in Markdown/HTML), CSRF, SSRF, path traversal · secrets in code/logs/history · token scope/expiry · rate limits and lockout abuse · file upload · dependency CVEs (audit tools) · headers/CSP · data exposure in API responses (prices, PII) · public-facing endpoints minimal.
- **Outputs:** findings with proof-of-concept *steps* (no weaponised exploit), severity, fix; fixes with tests if allowed.

## Performance engineer
- **Checklist:** baseline numbers first · p50/p95 latency, throughput, memory, bundle size, cold start · N+1 queries · load test of the critical path · regressions compared to baseline · recommendations ranked by gain/effort.

## Accessibility reviewer
- **Checklist:** keyboard-only path through main flows · focus visible · labels for inputs/icons · contrast in light and dark · reduced motion respected · screen-reader names for key controls · zoom 200% without horizontal scroll.

## UAT / field test coordinator
- **Mission:** prepare what only the owner/real users/real hardware can verify.
- **Outputs:** UAT checklist with numbered steps, expected result and a checkbox each, safety precautions, how to collect evidence (photo, log file path), how to roll back.
- **Done when:** the owner can run it without asking questions.
