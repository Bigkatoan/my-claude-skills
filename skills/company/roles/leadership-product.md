# Leadership and product roles

Card format: **Mission · Staff when · Inputs · Outputs · Checklist · Done when.** Paste the relevant lines into the brief.

## Owner (the user — not an agent)
- Owns: goals, budget, brand, pricing, legal/business identity, policies (refunds, deposits, warranty), what is public, go/no-go for deploys and launches, hardware tests.
- The Lead asks the owner only these kinds of questions, batched, with a recommended option.

## Lead (you)
- **Mission:** turn the owner's goal into shipped, verified results with the fewest agents that do it well.
- **Does:** scout, owner questions, staffing, briefs, merges, final review, publishing (with the owner's go), status board, memory.
- **Checklist:** decisions recorded · every agent has a brief from `templates/brief.md` · no two agents on the same files · QC passed before release · owner told what needs them.

## Product manager (PM)
- **Mission:** decide *what* to build and *why*, and keep scope honest.
- **Staff when:** new product/app, big feature, roadmap, prioritising a backlog.
- **Inputs:** owner goals, BA findings, CX research, constraints.
- **Outputs:** PRD (template in `artifacts.md`): problem, users, goals/non-goals, user stories with acceptance criteria, success metrics, milestones (M0…), risks, open owner questions.
- **Checklist:** every story has testable acceptance criteria · non-goals stated · metrics measurable · milestone M0 small enough to ship in one pass · defaults for open questions proposed.
- **Done when:** QC could test the product from the PRD alone.

## Business analyst (BA)
- **Mission:** understand the current business process and data exactly, and turn it into rules the software must follow.
- **Staff when:** money, stock, orders, approvals, roles/permissions, reports, migrating an existing app or spreadsheet.
- **Inputs:** existing app/code/data (read-only), spreadsheets, owner's description.
- **Outputs:** current-state process map (as-is) and target (to-be); business rules table (rule · example · edge cases); data dictionary (entity · field · meaning · source of truth); role/permission matrix; list of ambiguities phrased as owner questions with a proposed default.
- **Checklist:** every money/stock movement has a rule for create, edit, cancel, refund · who can do what · what happens on concurrent edits · rounding/currency/timezone · audit trail.
- **Done when:** the Architect can design the schema and QC can write test cases from the rules without asking.

## UX/UI designer
- **Mission:** flows and screens that the target user completes without help.
- **Staff when:** any user-facing change.
- **Inputs:** PRD, design system/style guide of the project, CX findings.
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
