# Requirements loop: from the customer's wish to an approved baseline

The user is the **customer (end user / client)**. The company (all agents) is the **vendor**. Nothing is built until the customer has approved the requirement set. The goal of the documents is twofold: the dev team can build every item **without impossible or contradictory demands**, and the customer gets what they actually need.

## The loop

```
Customer ──► BA ──► Tech Lead + SA ──► BA ──► Customer ──► (approve? → baseline) / (comments → next round)
```

| Step | Who | Does | Hands over |
|---|---|---|---|
| 1. Elicit | **BA** with the customer | Interviews the customer: goals, users, current way of working, must/should/could, constraints (budget, deadline, hardware, platforms), what "done" looks like to them. Uses `AskUserQuestion` (≤4 questions per call, recommended option first) plus open questions in chat. Never asks technical questions the vendor should decide. | Interview notes |
| 2. Draft | **BA** | Writes/updates **BRD**, **SRS**, **Feature list**, **Acceptance document** (draft). Every item has an ID and a source (what the customer said). | Draft set vN |
| 3. Review | **Tech Lead ‖ SA** (independent of each other) | SA: architecture, tech stack, systems, integrations, data, security, risks → **Architecture document**. Tech Lead: feasibility and effort per feature, dependencies, test approach, milestone cut. Both flag **"oái oăm" items**: contradictory, unmeasurable, unsafe, out of budget/time, legally risky, or impossible on the target platform, each with an alternative that still meets the customer's goal. | Review report + Architecture doc vN |
| 4. Reconcile | **BA** | Applies the review: rewrites flagged items with the alternatives, splits big features, moves items between must/should/could/won't, updates the acceptance tests. Prepares a **round summary** for the customer in plain language: what changed, why, what they must decide (with a recommended option). | Set vN+1 + round summary |
| 5. Customer review | **Customer** | Reads the summary and documents, comments or approves. | Comments or **approval** |

Repeat 1→5 until the customer approves explicitly ("duyệt", "đồng ý", "approve"). A silence or "ok tiếp đi" about something else is not approval; the BA asks.

**Approval creates the baseline:** documents become v1.0, the **Approved feature list** is frozen, and only then does Build start (Architect contract → builders → QC per feature).

**After the baseline:** any new or changed requirement is a **change request (CR)**. It goes through the same loop in small form (BA writes the CR with impact from Tech Lead/SA, the customer approves) and updates the Approved feature list with a new version. Builders never build unapproved items. Ideas the dev team has go to the BA as proposals, not into the code.

**Scale:** a new product or big feature gets the full set. A field bug or hotfix gets a one-page CR (problem, expected behaviour, acceptance tests). If the customer's bug report already states the expected behaviour unambiguously, the report counts as approval of the CR; otherwise the BA asks first.

## Roles in the loop
- **BA**: the only agent who talks to the customer about requirements. Owns BRD, SRS, Feature list, Acceptance document, round summaries, CR log. Writes in the customer's language.
- **SA (solution architect)**: owns the Architecture document and the tech-stack decision. Later writes the build contract.
- **Tech Lead**: owns feasibility, estimates, the milestone plan, and the dev team's commitment that **every approved feature will be delivered**.
- **QC**: reviews the Acceptance document before approval ("can I test every item as written?"). After build, tests **every** approved feature.
- **Lead**: runs the loop, keeps rounds short, never lets Build start before approval.

## Traceability (every ID links forward)
`BR-n` (BRD business requirement) → `FR-n` / `NFR-n` (SRS) → `F-n` (feature) → `AT-n` (acceptance test) → QC result. Every F has ≥1 AT; every BR is covered by ≥1 F or listed as won't-do with the customer's agreement.

## Where the documents live
In the project repo under `docs/requirements/`: `BRD.md`, `SRS.md`, `ARCHITECTURE.md`, `FEATURES.md`, `FEATURES-APPROVED.md`, `ACCEPTANCE.md`, `CHANGELOG.md` (rounds + CRs). Private products: private repo only. For each customer review, also give the customer an easy-to-read copy: a doc through the docs connector if one is attached, otherwise the file paths. The round summary always goes in chat.

---

## Templates

### BRD: Business Requirements Document (BA)
```
# <Project>: BRD v<x.y> (<date>) · status: draft | in review | approved
1. Background and problem (customer's words)
2. Business goals + success measures (measurable)
3. Stakeholders and users (who uses it, how often, skill level)
4. Current process (as-is) → target process (to-be)
5. Business requirements
   BR-1 <need> · priority Must/Should/Could/Won't · source <customer quote/date>
6. Business rules (ID · rule · example · edge cases)
7. Scope in / out · assumptions · constraints (budget, deadline, platforms, hardware, legal)
8. Risks · open questions (with proposed default)
```

### SRS: Software Requirements Specification (BA, reviewed by SA + Tech Lead)
```
# <Project>: SRS v<x.y>
1. Overview, glossary, references (BRD version)
2. Users/roles and permissions matrix
3. Functional requirements
   FR-1 <the system shall …> · traces BR-n · inputs · processing · outputs · errors/edge cases
4. Non-functional requirements (each measurable)
   NFR-1 performance (e.g. p95 < 300 ms) · NFR-2 safety · security · availability · platforms/OS/browsers/devices
   · usability (language, phone width, dark mode) · data retention · offline/recovery behaviour
5. Interfaces: UI screens list, APIs, hardware, external systems
6. Data: entities, fields, source of truth, migration
7. States and flows (diagram or table), including stop / failure / recovery paths
```

### Architecture document (SA)
```
# <Project>: Architecture v<x.y>
1. Context diagram (users, systems, hardware)
2. Tech stack table: layer · choice · version · why · alternatives rejected · licence
3. Components and responsibilities; deployment (where it runs, per platform)
4. Data model + storage; integrations and APIs
5. Cross-cutting: auth, security, safety, logging/monitoring, config, i18n, updates/rollback
6. NFR → how the design meets each one
7. Risks and spikes (what must be proven early), decisions log (ADR-n)
8. Review of requirements: flagged items (FR/F id · problem · proposed alternative)
```

### Feature list (BA + Tech Lead)
| ID | Feature | User value | Traces (BR/FR) | Priority | Effort (Tech Lead) | Milestone | Acceptance tests | Status |
|---|---|---|---|---|---|---|---|---|
| F-1 | | | BR-1, FR-2 | Must | S/M/L | M0 | AT-1, AT-2 | proposed / flagged / ready |

### Approved feature list (frozen at approval; new version per CR)
```
# Approved features v<1.0> · approved by customer on <date> (quote of approval) · baseline docs: BRD vX, SRS vY, Arch vZ
```
| ID | Feature | Milestone | Acceptance tests | Dev status | QC result | In release |
|---|---|---|---|---|---|---|
| F-1 | | M0 | AT-1, AT-2 | not started / in progress / done | PASS / FAIL / not tested | yes / no (why) |

### Acceptance document (BA writes, QC reviews before approval, QC executes after build)
```
# <Project>: Acceptance v<x.y>
Environment: exact artifact (version, install command), OS/devices/hardware, test data
AT-1 (F-1) <title>
  Preconditions · Steps (numbered, as a user does them) · Expected result · Evidence to keep (screenshot/log)
  Result: PASS / FAIL / NOT VERIFIED (why) · tester · date · artifact version
Sign-off: QC <date>  ·  Customer acceptance <date>
```

### Round summary (BA → customer, in chat)
```
Round <n> · documents v<x.y> (links)
What changed since last round (3-7 bullets, plain language)
Items we propose to change and why (F-id · your request · problem · our proposal)
Decisions you need to make (with our recommended option)
To approve, reply "duyệt" (or comment on the items).
```
