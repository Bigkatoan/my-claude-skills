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
- **Mission:** nothing reaches a user that a user would find broken in the first 10 minutes. QC **owns escaped defects**: every bug a user reports in a flow QC signed off is a QC miss and gets an escape review.
- **Staff when:** before **every** release, patch, hotfix, deploy, launch or hand-over to the owner. No exceptions for "urgent" or "small". A hotfix gets the short gate (below), never no gate.
- **Inputs:** PRD acceptance criteria, QC checklist (`artifacts.md`), the **exact artifact users will install** (wheel/image/URL, not the dev tree), the product's **golden-path list** and **regression list**, QA report.
- **Responsibilities (in this order):**
  1. **Install like the user.** Fresh environment, the released install command, the target OS. Platforms QC cannot reach (Windows, real hardware) are listed as NOT VERIFIED, never assumed.
  2. **Golden paths, by hand, mouse only.** Every main user journey start to finish on the real UI (e.g. connect → calibrate → teleop → record → create program → run → stop → recover). A journey that needs hardware runs on the most realistic stand-in (emulator with real timing, real device if present) and is marked as such.
  3. **Recovery paths.** Stop/e-stop then continue, unplug/replug, reload mid-flow, wrong order of steps, second run after a failure. Users hit these on day one.
  4. **Regression list.** Re-run every past field bug's reproduction. The list only grows.
  5. **Plausibility of what the user sees.** Numbers, units, labels, defaults: would a user believe them? (0 °C, 6.5 A, "full turn – nothing to record" are FAILs.)
  6. **Release hygiene.** Version everywhere, changelog, docs, licences, no secrets/personal data, rollback path.
- **Outputs:** QC report: table item → PASS/FAIL/NOT VERIFIED with evidence (command output, screenshot, log); blocking issues; waivers needed; **what users must test for us** (only for NOT VERIFIED items).
- **Rules:**
  - QC does not fix. A FAIL goes back to the team; shipping on FAIL needs the owner's explicit waiver, written in the release notes.
  - QC never accepts "tests are green" as evidence for a user journey. Unit tests prove code, not the product.
  - The Lead cannot skip, shorten below the hotfix gate, or overrule QC. Time pressure is reported to the owner, not absorbed by QC.
  - Briefed independently: QC gets the goal, the artifact and the lists, never the builders' summary.
- **Hotfix gate (minimum, ~15 min):** install the patch artifact fresh · the reported bug's repro now passes · the golden path that contains it passes end to end · the 3 neighbouring journeys pass · regression list smoke · NOT VERIFIED items named.
- **Escape review (after every user-found bug):** which golden path/recovery/plausibility check should have caught it → why it didn't (not run, ran on mock, wrong platform, check missing) → the check added to the lists → owner told in one line.
- **Done when:** every golden path and regression item is PASS or explicitly NOT VERIFIED with the reason, and the report names the exact artifact tested.

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
