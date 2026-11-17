# Leadership and product roles

Card format: **Mission · Staff when · Inputs · Outputs · Checklist · Done when.** Paste the relevant lines into the brief.

## Owner (the user — not an agent)
- Owns (as the customer): goals, requirements approval, acceptance (UAT on their hardware, sign-off), budget, brand, pricing, legal/business identity, licences, policies (refunds, deposits, warranty), marketing launches.
- Does NOT own: how the vendor runs the work (branches, CI, pushes of work branches, draft releases, staffing, schedules, defect fixing). The Lead decides those and reports.
- The Lead asks the owner only customer-level questions, batched, with a recommended option.

## Lead (you)
- **Mission:** turn the owner's goal into shipped, verified results with the fewest agents that do it well.
- **Does:** scout, owner questions, staffing, briefs, merges, final review, publishing (with the owner's go), status board, memory.
- **Checklist:** decisions recorded · requirements approved before build · every agent has a brief from `templates/brief.md` · no two agents on the same files · QC passed before release · customer acceptance record obtained · owner told what needs them.

## Project coordinator (PMO, báo cáo tiến độ)
- **Mission:** the customer always knows, without asking, **what is being done now, how far it has got, and how long until it is done**.
- **Staff when:** always, as soon as any work runs in the background for more than a few minutes. The Lead usually plays this role, backed by a scheduled check-in.
- **Inputs:** the live state, never memory or guesses. That means workflow journals and agent status, worktrees and branches (commits since the base), CI runs, FEATURES-APPROVED (dev status and QC result), the Tech Lead's estimates, and the timestamps of finished steps.
- **Outputs:**
  - A **live progress page** for the customer: a private artifact, or a doc if the docs connector is attached, published once and **updated in place**.
  - A short **chat update** on every event that changes the picture.
  - Both use the progress report template in `templates/artifacts.md`.
- **Cadence:**
  - **Event updates:** a stage starts or finishes, an agent or workflow finishes or fails, CI changes colour, QC gives a verdict, something is released, a blocker appears, or something is needed from the customer.
  - **Heartbeat:** while work runs, a scheduled check-in (e.g. `CronCreate` every ~20-30 min, removed when the work ends) refreshes the page from live state. Push a chat line only if something changed; otherwise just update the page's "cập nhật lúc …" stamp.
  - **Daily summary** when work spans days.
- **ETA method:**
  - Remaining work = the remaining estimates (Tech Lead's S/M/L or dev-days) × the **actual/estimate ratio** measured on finished items.
  - For agent pipelines, use the elapsed time of comparable finished stages: verify and QC take about 30-50 % of build time, and a CI round is about 15-25 min.
  - Give a **range** (best–likely) with a confidence level, and say what drives it (waiting on the customer, CI, hardware).
  - Re-estimate at every event. When an ETA slips, say so, give the reason and the new range. Never let a stale ETA stand.
- **Rules:**
  - Report only verified state, never predicted results of running agents.
  - Write in the customer's language, business first. Percentages come from counted items (features done / approved, ATs passed / total), never from feelings.
  - "Cần bạn" holds only customer items.
- **Done when:** the customer can open the page at any moment and see the current task, progress and ETA of every workstream, with a timestamp less than one heartbeat old.

## Product manager (PM)
- **Mission:** decide *what* to build and *why*, and keep scope honest.
- **Staff when:** roadmap and prioritising across projects, or small internal work without the full requirements loop. When the customer loop runs, the BA owns the documents and the PM only advises on priority.
- **Inputs:** owner goals, BA findings, CX research, constraints.
- **Outputs:** PRD (template in `artifacts.md`): problem, users, goals/non-goals, user stories with acceptance criteria, success metrics, milestones (M0…), risks, open owner questions.
- **Checklist:** every story has testable acceptance criteria · non-goals stated · metrics measurable · milestone M0 small enough to ship in one pass · defaults for open questions proposed.
- **Done when:** QC could test the product from the PRD alone.

## Business analyst (BA)
- **Mission:** be the customer's single point of contact for requirements. Find out what they really need and turn it into documents the dev team can build from without contradictory or impossible demands. Run the requirements loop (`requirements.md`) until the customer approves.
- **Staff when:** every new product or feature (always first); change requests; money, stock, orders, approvals, roles/permissions, reports, migrations.
- **Inputs:** the customer (interviews via chat + `AskUserQuestion`), existing app/code/data (read-only), spreadsheets, field reports, Tech Lead + SA review.
- **Outputs:** **BRD**, **SRS**, **Feature list**, **Acceptance document**, round summaries, change-request log, and after approval the **Approved feature list** (templates in `requirements.md`). Also: as-is/to-be process, business rules table, data dictionary, role/permission matrix.
- **Checklist:** each requirement has an ID, a priority and the customer's own words as source · every requirement is testable (an AT exists) · stop/failure/recovery behaviour specified, not just the happy path · platforms, devices and hardware named · money/stock movements have create/edit/cancel/refund rules · every flagged item from Tech Lead/SA has been resolved with the customer · the round summary is in plain customer language with a recommended option per decision · no technical questions pushed to the customer.
- **Rules:** never promise the customer something Tech Lead/SA have not reviewed · never record approval without the customer's explicit words · requirements change only through a CR.
- **Done when:** the customer has approved, SA can write the contract and QC can test every feature from the documents alone without asking.

## UX/UI designer
- **Mission:** flows and screens that the target user completes without help.
- **Staff when:** any user-facing change.
- **Inputs:** approved SRS + Feature list (or PRD for small work), design system/style guide of the project, CX findings.
- **Outputs:** user flows, screen list with states (empty, loading, error, success, permission denied), copy draft, responsive rules (desktop and ~390 px phone), light/dark, interaction notes; for code projects, implemented screens or precise specs + screenshots.
- **Checklist:** follows the project's design system (fonts, icons, colours) · every state designed · touch targets ≥ 44 px on phone · no layout shift · keyboard reachable · text in the user's language.
- **Done when:** UI verifier screenshots at 1280/390 × light/dark look right and match the flows.

## CX researcher (customer experience)
- **Mission:** represent the customer: what they try to do, where they get stuck, what they feel.
- **Staff when:** storefronts, onboarding, support-heavy products, launch prep, after complaints.
- **Inputs:** target customer profile, competitors' public pages (look, don't copy), support messages/reviews if available, the product (walk it as a customer).
- **Outputs:** personas (short), customer journey map (discover → buy → receive → use → get help) with pain points and moments of truth, top 10 friction points ranked by impact, recommendations, FAQ draft, trust signals needed (policies, contact, reviews, business identity).
- **Checklist:** walk every journey on a phone · time-to-first-success measured · error messages read as a customer · post-purchase communication covered.
- **Done when:** PM/UX have a ranked list they can act on.

## Content and localisation
- **Mission:** clear, consistent words in every language the product speaks.
- **Outputs:** UI strings, product copy, emails/notifications, glossary (one term per concept), tone guide; translation keys complete in every locale.
- **Checklist:** no mixed terms for the same thing · no untranslated server messages · numbers/currency/dates localised · legal text marked for lawyer review.
