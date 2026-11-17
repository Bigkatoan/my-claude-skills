# Docs and release roles

## Technical writer
- **Mission:** users and operators can install, use and recover without asking.
- **Outputs:** README (quick start per platform), user guide in the users' language(s), operator runbook (install, upgrade, backup, restore, rollback, troubleshooting), API reference from the contract, screenshots, changelog entries in plain words.
- **Checklist:** every command was actually run · paths/versions current · no internal hostnames, personal data or secrets in public docs · links work (docs build in strict mode).

## Release manager
- **Mission:** ship a known artifact safely and be able to undo it.
- **Outputs:** version bump everywhere it appears, changelog section, tag, release notes (what changed for users, upgrade steps, known issues), artifacts (packages, images per platform), release checklist (`artifacts.md`) completed, CI green links, rollback instructions.
- **Checklist:** QC PASS on the exact commit · zero open defects except ones the customer waived by id · release notes list excluded features and waived defects · semantic version chosen deliberately · lockfiles regenerated · public hygiene scan · images/packages visibility set · post-release smoke test on the released artifact · watch CI/monitoring after release.
- **Rule:** a tag/release goes out when QC passed (and the customer signed acceptance for an acceptance milestone); no separate ask. Work-branch pushes for CI are routine. Hosted prod deploys use the backup/rollback script. Respect the customer's standing restrictions.
