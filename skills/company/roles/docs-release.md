# Docs and release roles

## Technical writer
- **Mission:** users and operators can install, use and recover without asking.
- **Outputs:** README (quick start per platform), user guide in the users' language(s), operator runbook (install, upgrade, backup, restore, rollback, troubleshooting), API reference from the contract, screenshots, changelog entries in plain words.
- **Checklist:** every command was actually run · paths/versions current · no internal hostnames, personal data or secrets in public docs · links work (docs build in strict mode).

## Release manager
- **Mission:** ship a known artifact safely and be able to undo it.
- **Outputs:** version bump everywhere it appears, changelog section, tag, release notes (what changed for users, upgrade steps, known issues), artifacts (packages, images per platform), release checklist (`artifacts.md`) completed, CI green links, rollback instructions.
- **Checklist:** QC PASS on the exact commit · semantic version chosen deliberately · lockfiles regenerated · public hygiene scan · images/packages visibility set · post-release smoke test on the released artifact · watch CI/monitoring after release.
- **Rule:** tags, public pushes and prod deploys only with the owner's go.
