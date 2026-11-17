# Playbooks (line-ups to start from — remove roles you don't need)

`→` = sequential, `‖` = parallel. Bold = gate that must pass before moving on.

## New product / app (e.g. a storefront, an internal tool)
Discover: BA ‖ CX researcher ‖ (legal if personal data or money) → Define: PM writes **PRD** (owner confirms open questions) → Design: UX/UI ‖ Architect (**contract**, mock backend) → Build M0: frontend ‖ backend (or one full-stack agent for small apps, against the mock) → QA (e2e + screenshots) ‖ security → **QC** → owner demo → Release (DevOps, writer) → Launch (marketing, support) when the owner says go.

## Feature in an existing product
Lead scouts → (BA if business rules) → Architect **contract** → builders A ‖ B ‖ UI → Integrator (owner's example end to end) → QA safety/backend ‖ QA UI/e2e → **QC** → release manager.

## Audit / polish an existing product ("làm nét lại sản phẩm")
Reviewers in parallel, one dimension each: security ‖ data/money integrity (BA) ‖ UX/CX ‖ ops/DevOps ‖ code quality/architecture → Lead dedups and ranks → fixer on a branch for critical issues only → independent verifier → backlog in waves (Wave 1 critical fixes, Wave 2 foundation, Wave 3 product/UX, Wave 4 new capabilities) + owner questions → **QC** before deploying Wave 1.

## Launch / go-to-market
CX researcher (journeys, trust signals) ‖ marketing (positioning, SEO, launch calendar) ‖ legal (policies, consent) ‖ finance (pricing proposals) → content (copy in all languages) → support (FAQ, macros) → **QC** of the public site (links, policies, prices, forms, phone layout, speed) → owner approves every public text and price.

## Release / deploy
Release manager (version, changelog, artifacts) → **QC** on the exact artifact → DevOps: backup → wait for running jobs → switch → smoke checks → auto-rollback on failure → monitor → report. Schedule outside working hours unless the owner says now.

## Incident / production bug
Lead triages (impact, since when, who) → SRE stabilises (rollback or mitigate) → developer finds root cause and fixes with a failing-first test → QA regression → **QC** → patch release → short post-mortem (cause, fix, prevention) to the owner.

## Bug reported from the field (user's machine/platform)
Reproduce on the same platform (CI runner or container) → fix on `fix/*` branch with a test → add the repro to the **regression list** and that platform to CI permanently → **QC hotfix gate on the built artifact (mandatory, even when the owner says "sửa nhanh")** → patch release → **QC escape review** (why we missed it, which check was added) → reply text for the user (what to do now, workaround meanwhile, what we could not verify on their platform).
Speed comes from a short gate, never from skipping it. Several bugs in one report → one patch with one QC pass, not one release per bug.

## Migration / repo split / platform move
Architect plans the cut (what moves, what stays, interfaces kept stable) → builder creates the new home locally with full checks → security/hygiene scan → owner go → publish → second builder removes the old copy and points docs to the new home → CI watch on both → release notes.

## Research / decision
2-3 agents take different angles (cost-first, risk-first, user-first) → judges score against the owner's criteria → Lead writes a one-page recommendation with the runner-up ideas grafted in.
