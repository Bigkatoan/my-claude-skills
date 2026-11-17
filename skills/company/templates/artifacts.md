# Artifact templates

Requirement documents (BRD, SRS, Architecture, Feature list, Approved feature list, Acceptance) live in `requirements.md`. The PRD below is the PM's short form for small internal work.

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
| 1 | Every feature on the Approved feature list tested against its ATs on the release candidate (`<id>`); failing/untested features excluded and listed | | |
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
| 12 | Installed fresh from the released artifact with the user's command, on each target OS (else NOT VERIFIED) | | |
| 13 | Every golden path done by hand on the installed artifact | | |
| 14 | Recovery paths: stop/e-stop → continue, unplug/replug, reload mid-flow, wrong step order, rerun after failure | | |
| 15 | Regression list (all past field bugs) re-run | | |
| 16 | Every number/unit/label the user sees is plausible | | |
| 17 | NOT VERIFIED items listed with what the user must test | | |
Verdict: PASS / FAIL (blocking items) / PASS with owner waivers (list).

## Golden paths + regression list (QC owns, per product, kept in the repo e.g. `docs/qc/`)
```
GP-1 <journey>: step → expected · step → expected ...   (platform, stand-in used)
REG-<n> <field bug title> (vX.Y.Z, reported <date>): repro steps → expected now
```

## Escape review (QC, after each user-found bug)
Bug · version shipped · which GP/REG/check should have caught it · why missed (not run / mock only / platform / check missing / Lead skipped QC) · check added (id) · owner told (yes).

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

## Progress report (Project coordinator → customer; live page + chat)
```
Cập nhật lúc <HH:MM dd/mm> · tổng thể <x>% (<done>/<total> <unit: tính năng / bài nghiệm thu / bước>) · dự kiến xong <range> (độ tin cậy <cao/vừa/thấp>)
```
| Mảng việc | Đang làm gì (ngay lúc này) | Tiến độ (đếm được) | Dự kiến xong | Trạng thái |
|---|---|---|---|---|
| <workstream> | <current step, who> | <3/7 bước · 12/44 tính năng> | <time range> | Đúng hạn / Chậm (lý do) / Bị chặn (bởi gì) / Xong |

**Vừa xong:** <last 3 events with time>  
**Tiếp theo:** <next step + when>  
**Rủi ro / thay đổi dự kiến:** <ETA changes with reason>  
**Cần bạn:** <customer items only, or "không có">

Chat version: 2-4 lines (now · progress · ETA · cần bạn).

## Retro (Lead)
Keep · Change · Try next time · Memory updated (yes/no, what).
