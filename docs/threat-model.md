# Threat model

What VouchRail defends against, what it doesn't, and the operational controls that close the gap. Skim this before deciding whether VouchRail fits your evidentiary needs — and again before writing any external-facing claim about chain integrity.

## In scope

VouchRail's cryptographic surface area covers:

- **Tamper of historical records.** Any byte change to a stored entry — including silent edits by an operator, a misconfigured ETL job, or a malicious DB administrator — breaks `entryHash` at that record and chain linkage at every record after it. `vouchrail verify` reports the first broken index and the failure mode (`entry_hash_mismatch` / `chain_link_mismatch` / `genesis_link_mismatch`).
- **Reordering or deletion.** Removing or reordering entries breaks the `previousEntryHash` chain link at the cut point. Verification flags it.
- **Cross-language drift.** TypeScript and Python SDKs produce byte-identical canonical bytes via RFC 8785 JCS + ECMA-262 `NumberToString`. Sixteen conformance vectors in CI fail the build on any divergence.
- **Incomplete audit exports.** `vouchrail export` walks the same storage layer as `verify`; an exported JSONL is verifiable by any party with the same CLI.
- **Weak internal audit tables.** A database table with no verification story is not evidence. VouchRail entries carry their own integrity proof — admissibility no longer depends on operator testimony about the DBA's discipline.

## Out of scope

VouchRail does NOT defend against:

- **Compromise of both signing key and storage.** An attacker holding `kms:Sign` and write access to the storage backend can rewrite history end-to-end. Mitigation: split the signing role from the storage-write role; pair with [chain-head anchoring](#chain-head-anchoring) so externally pinned heads catch retroactive rewrites.
- **Operator-initiated deletion when retention is unconfigured.** Local disk has no Object Lock. S3 without Object Lock can be emptied by anyone with `s3:DeleteObject`. The chain detects deletion *given the surviving entries*, but the deleted span cannot be reconstructed. Mitigation: [storage hardening](./storage-hardening.md).
- **Application lies before write.** If your app feeds the SDK a falsified `outputDecision`, VouchRail signs the falsification faithfully. The audit log is a record of *what the system said it did*, not of objective ground truth.
- **Bad governance process.** Reason codes, human-review fields, and operator IDs are recorded as supplied. Missing or rubber-stamped human-review entries are a process failure that VouchRail records but does not detect.
- **Legal sufficiency by itself.** Article 12 admissibility depends on key custody, retention configuration, periodic verification, and separation of duties — operational controls VouchRail enables but does not enforce. See [legal/limitations.md](../legal/limitations.md).
- **Model provider correctness.** A model that hallucinates is still a model. VouchRail records the prompt, the output fingerprint, and the model version — enough to attribute the hallucination to a specific model + prompt pair, not to prevent it.
- **PII leakage outside redactable string fields.** Regex redaction handles text input. Binary blobs (images, audio) are fingerprinted, not redacted. `outputDecision` is your structured field — keep PII out of it. See [PII redaction](./pii-redaction.md) and [PII + erasure](./pii-and-erasure.md).

## Threat scenarios

| Scenario                                            | Detected by VouchRail            | Required hardening                                  |
| --------------------------------------------------- | -------------------------------- | --------------------------------------------------- |
| DBA edits one record                                | Yes (`entry_hash_mismatch`)      | None                                                |
| Operator deletes last 30 days                       | Partial (linkage break visible)  | Object Lock + chain-head anchor                     |
| Attacker has signing key, replaces all entries      | No                               | Anchored chain head + separation of duties          |
| Insider re-signs altered chain in offline copy      | Yes (anchor mismatch on rejoin)  | Periodic anchor verification                        |
| App passes wrong `outputDecision`                   | No                               | Application-side validation; reviewer attestation   |
| Forgotten KMS key rotation                          | No                               | Key-id field on entries + verification dashboards   |
| PII written to `outputDecision` then GDPR-erased    | No (chain is intact regardless)  | Pre-write validation; structured-field discipline   |

## Recommended hardening

Beyond installing the SDK:

1. **KMS-backed signer.** Inline HMAC is for dev. Production signers should run from KMS/HSM/Vault with sign-only permissions. See [Signing keys](./signing-keys.md).
2. **WORM storage.** S3 Object Lock in Compliance mode with retention ≥ your regulatory minimum. See [Storage hardening](./storage-hardening.md).
3. **Separated duties.** Application role holds `s3:PutObject` + `kms:Sign`. Storage admin role holds bucket-policy edit. Key admin role holds `kms:CreateKey` / `kms:ScheduleKeyDeletion`. No role holds all three.
4. **Periodic verification.** A scheduled job runs `vouchrail verify` over the live store and alerts on non-zero exit. Cron + paging beats discovery-by-regulator.
5. **Chain-head anchoring.** Run `vouchrail anchor` at interval N. Persist the head to a tamper-resistant external location: a Git tag, a customer-controlled webhook, an S3 bucket in a separate account, an email to a compliance mailbox. A divergent head means a retroactive rewrite. See [CLI usage — anchor](./cli.md#anchor).
6. **Backup the token store separately from logs.** If you ever need to re-identify a token (e.g., regulator request), the token store must outlive incidents that delete the logs. Treat it as Tier-0 data.

## Chain-head anchoring

`vouchrail anchor --storage-dir ./audit-logs --system-id <id> --output chain-head.json` writes the last sequence number, last entry hash, and last entry's signature to a portable JSON file. Copy this file out of the trust boundary that holds the logs.

The narrow defense it gives you: an attacker who later rewrites history must also rewrite every anchored head wherever you stashed them. Stash them in places the attacker can't reach (different account, different vendor, paper print-out for the regulator) and the rewrite is detectable.

What it does not give you: timestamping (the anchor file says when YOU wrote it, not when the chain reached that head). For an unforgeable timestamp, pin the anchor in a system whose timestamp you can later prove independently — e.g., a Git commit signed by a key under a different custody chain, or a transparency log.

## Reporting issues

Suspected verification bug or cryptographic weakness: see [SECURITY.md](../SECURITY.md). Do not file public issues for embargoed disclosures.
