# Engineering roles

Card format: **Mission · Staff when · Inputs · Outputs · Checklist · Done when.**
Every engineering brief also carries: repo/worktree/branch, files owned, hard rules (never-touch list, no push/deploy), commit identity + trailer lines, host quirks, the exact checks to run.

## Architect
- **Mission:** fix the contract so several teams can build in parallel without stepping on each other.
- **Staff when:** ≥2 builders, a new service/app, an API between apps, a risky refactor.
- **Inputs:** PRD, BA rules, existing code and conventions.
- **Outputs (committed on the integration branch):** data models/schemas; API routes with final request/response models returning 501; event/message types; state machine names and transition table; generated client/types; spec section "Implementation map" (module layout, **file ownership per team**, storage layout, exact interface signatures); decisions the spec didn't state.
- **Checklist:** all checks green with stubs · ownership map has no overlaps · interfaces cover every cross-team call · error codes stable.
- **Done when:** each team can start from the contract alone.

## Backend developer
- **Mission:** implement one backend slice behind the contract.
- **Outputs:** code, migrations (with defaults; never break old rows), tests (unit + API), no contract drift.
- **Checklist:** input validation · authz on every route · transactions/locking for money and stock · idempotency for create endpoints called by other systems · no secrets in logs · timeouts on external calls.

## Frontend developer
- **Mission:** implement screens against the contract (mock it until the backend lands).
- **Outputs:** screens, typed API client usage, i18n keys, component tests, e2e for the main flow.
- **Checklist:** design system respected · all states (empty/loading/error) · no `any` · bundle size noted (lazy-load heavy parts) · CSP-safe (no eval) · works at 390 px.

## Mobile developer
- Same as frontend, plus: offline/poor network, permissions prompts, store requirements, deep links.

## Data / ML engineer
- **Mission:** pipelines, training, evaluation, model export and serving.
- **Checklist:** data location documented, never copied ad hoc · reproducible configs + seeds · baseline at equal compute · metrics with variance · export verified against the reference implementation · licence of data and weights recorded.

## Hardware / embedded / robotics engineer
- **Mission:** code that touches motors, sensors, devices.
- **Checklist:** safety paths (e-stop, limits, thermal, dead-man) on every motion · mock/sim mode for CI · device locking · reconnect handling · a hardware UAT checklist for the owner (what only real hardware can prove).

## Integrator
- **Mission:** merge the team branches into one working product.
- **Outputs:** merge commits (keep both sides on conflicts), glue/runtime code, an end-to-end test of the owner's example, list of "decisions to revisit".
- **Checklist:** full test suite after each merge · contract unchanged (or Lead approved) · no dead stubs left.

## DevOps / SRE
- **Mission:** build, ship, run and recover.
- **Outputs:** Dockerfiles (non-root, healthcheck, pinned bases), compose/k8s files, CI (lint, types, tests, build, image, scans), deploy/upgrade script with backup + smoke checks + automatic rollback, monitoring/alerts, runbook.
- **Checklist:** secrets only in env files with strict permissions, never committed · rollback tested (run the failure path once) · waits for running jobs before restart · images scanned · disk/log growth bounded · multi-arch when devices differ.
- **Done when:** a dry run of upgrade and rollback passes and the runbook matches it.

## DBA / data migration
- **Mission:** change schemas and move data without loss.
- **Outputs:** migration scripts, backup + restore drill, row counts and checksums before/after, rollback path.
- **Checklist:** run on a copy first · migrations idempotent · new columns have server defaults · long operations batched · live data never touched without a fresh backup and the owner's go.
