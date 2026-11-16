# Artifact templates

## PRD (PM)
```
# <Product/feature> — PRD v0.1 (<date>)
Problem · Users (personas) · Goals / Non-goals · Success metrics
User stories:
  US-1 As a <user> I want <action> so that <outcome>.
       Acceptance: Given <state> When <action> Then <result>  (one line per criterion, testable)
Scope by milestone: M0 (smallest shippable) · M1 · M2
Business rules (from BA) · Data touched · Roles/permissions
Risks · Dependencies · Open questions for the owner (with proposed default)
```

## Business rules table (BA)
| ID | Rule | Example | Edge cases | Source |
|---|---|---|---|---|

## Test plan (QA)
```
Scope · Environments (mock/staging, browsers, widths, themes)
Matrix: acceptance criterion → test (unit/API/e2e/manual) → status
Exploratory charters (30 min each): <area + what to try to break>
Data: fixtures/accounts per role
Exit criteria: all criteria covered, no open critical/high defects
```

## Defect
`[severity] title` · steps · expected · actual · evidence (path/log) · build/commit · suspected area.

## QC checklist (release gate)
| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | Every PRD acceptance criterion passes on the release candidate (commit/image `<id>`) | | |
| 2 | Full CI green on that commit | | |
| 3 | Main flow done by hand as a real user (desktop + phone, light + dark) | | |
| 4 | Error and empty states readable, in the user's language | | |
| 5 | Permissions: each role sees only what it should | | |
| 6 | Money/stock/data integrity rules hold (cancel, edit, concurrent) | | |
| 7 | Security findings closed or waived by owner | | |
| 8 | Version, changelog, docs, screenshots updated | | |
| 9 | No secrets, personal data, internal hostnames in public artifacts; licences/attribution present | | |
| 10 | Backup + rollback path exists and was tested | | |
| 11 | Monitoring/health check covers the new parts | | |
Verdict: PASS / FAIL (blocking items) / PASS with owner waivers (list).

## Release checklist (release manager)
Version bumped everywhere · lockfiles · changelog · QC PASS · tag (owner go) · artifacts per platform · visibility of packages/images · release notes (changes, upgrade, known issues, rollback) · post-release smoke on released artifact · CI watched to green.

## Launch plan (marketing + CX)
Audience · promise · channels + dates · assets (copy, images, video) · landing/SEO checklist · tracking (UTM) · support readiness (FAQ, macros, who answers, hours) · success metric + review date.

## Status board (Lead → owner)
| Phần | Trạng thái |
|---|---|
| <workstream> | Xong / Đang làm / Chưa tới lượt / Cần bạn |

**Cần bạn:** 1. … 2. …  
**Tiếp theo:** <one line>

## Retro (Lead)
Keep · Change · Try next time · Memory updated (yes/no, what).
