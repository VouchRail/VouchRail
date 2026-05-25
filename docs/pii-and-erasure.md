# PII and erasure

How VouchRail reconciles Article 12 retention (≥ 6 months of auditable records) with GDPR erasure (delete a data subject's identifiers on request). The chain stays cryptographically intact; only the lookup table shrinks.

For pattern definitions and config keys, see [PII redaction](./pii-redaction.md). This page covers the operational model — what is stored where, what erasure actually removes, and what cannot be undone if raw PII was ever written.

## The split

The pseudonymize strategy creates two distinct artifacts per entry:

| Artifact                   | Lives where                                | Contains                                    | Erasable? |
| -------------------------- | ------------------------------------------ | ------------------------------------------- | --------- |
| Audit log entry            | Storage backend (local FS / S3)            | Opaque tokens `pii:7a3c8f…` + non-PII fields | No — chain integrity |
| Token store row            | Separate store (memory / SQLite / custom)  | Token → original-value mapping              | Yes — `eraseCase()` |
| Input/output fingerprints  | Audit log entry, derived from raw input    | SHA-256 of canonicalized payload            | No — derived data |

The audit log entry never holds the original PII string. The token store holds the only bridge between the token and the original value. Delete the bridge → tokens become opaque forever; the chain still verifies.

## What erasure deletes

```ts
await tokenStore.eraseCase('candidate-12345');
```

After this call:

- Every row in the token store whose `caseId === 'candidate-12345'` is gone.
- `reveal(token)` for any of those tokens returns `null` permanently.
- The audit log entries are byte-for-byte unchanged. Their `entryHash` recomputes to the same digest. `vouchrail verify` returns valid.
- The fingerprints (`inputFingerprint`, `outputFingerprint`) remain because they identify the *fact* of a specific request having occurred, not the PII contents. A regulator asking "did this person's data flow through your system" can confirm yes via fingerprint match if they can re-derive the fingerprint from their copy of the data; once the token store is wiped, they cannot reverse the token back to the original value.

The chain still tells the auditor:

- A request was made at time T against system S for case X.
- The model returned a structured decision with fingerprint F.
- A human reviewer (if any) approved/overrode at time T'.

It no longer tells anyone:

- What raw email / name / SSN string was in the input.

That is the GDPR right-to-erasure outcome, satisfied without breaking the audit chain.

## What erasure does NOT delete

- **Fingerprints.** SHA-256 of canonicalized input is one-way. It cannot be reversed without the original input. It is also not reversed *by* erasure — a future regulator who already has the original input can re-derive the fingerprint and prove the case ran. This is intentional: erasure deletes the operator's ability to reverse-lookup, not the cryptographic record of activity.
- **PII written to non-redacted fields.** If your application puts raw PII into `outputDecision` or `reasonCodes`, redaction does not see it. The chain locks in those bytes. Erasure cannot remove them without breaking the chain. Mitigation: keep PII out of structured decision fields; pre-validate at the application layer.
- **PII in binary blobs.** Images, PDFs, audio. The SDK fingerprints binary payloads but does not redact inside them. If your pipeline includes image OCR or speech-to-text, redact the *text output* before VouchRail sees it.
- **Token-store backups.** Token-store rows live in your token-store backups. Erasure on the live store is meaningless if the backups are not also processed. Treat token-store backups as in-scope for GDPR DSAR / erasure workflows.

## Recommended defaults

For new VouchRail deployments handling personal data:

```ts
piiRedaction: {
  enabled: true,
  strategy: 'pseudonymize',
  patterns: { email: true, phone: true, ssn: true, ipAddress: true, creditCard: true, iban: true },
  tokenStore: { type: 'sqlite', path: './audit-state/pii.sqlite' },
}
```

Then:

1. Pre-validate that no PII reaches `outputDecision`, `reasonCodes`, or any non-redacted field. A schema check at the application layer is cheaper than a post-hoc audit.
2. Treat `./audit-state/pii.sqlite` as Tier-0 sensitive data — encrypted at rest, restricted to the application role and a small DSAR-handler role.
3. Wire `eraseCase` to your customer-deletion endpoint; a DSAR request that hits the token store within minutes of confirmation beats a quarterly cleanup batch.

## What is stored, fingerprinted, dropped

For a typical request through `audit.wrap(...)`:

| Field                | Storage form                                         | Original PII recoverable? |
| -------------------- | ---------------------------------------------------- | ------------------------- |
| `caseId`             | As-supplied                                          | If you put PII in caseId, yes (don't do that) |
| Redacted input text  | Original string with PII spans replaced by tokens    | Only via token store      |
| `inputFingerprint`   | SHA-256 of canonicalized original input              | No (one-way)              |
| `outputDecision`     | As-supplied (your structured field)                  | Yes if you put PII here   |
| `outputFingerprint`  | SHA-256 of canonicalized output                      | No (one-way)              |
| `operatorId`         | As-supplied                                          | If operator IDs encode PII, yes |
| `reasonCodes`        | As-supplied                                          | Should be a stable code set, not free text |

The redactor walks `input` looking for known patterns. It does NOT walk `outputDecision` (a structured decision field that should not contain free-text PII), `reasonCodes` (regulator-shaped code list), or `caseId` (your stable identifier — pseudonymize at the application layer if needed).

## Article 12 × GDPR

The pseudonymize-with-token-escrow pattern is the legal pattern this implements. Whether a specific supervisory authority accepts it as sufficient for both regimes simultaneously is a question for your counsel — VouchRail provides the infrastructure, not the legal opinion. See [legal/limitations.md §8](../legal/limitations.md#8-article-12--gdpr-resolution-is-a-pattern-not-a-guarantee).

If your counsel disagrees, the `remove` strategy drops the original text entirely (`[REDACTED]`). The chain still verifies, but you lose the ability to honor a regulator's "show me the input" request — irreversibly. Pick the strategy that matches the worst-case investigator you might face.

## Warning: raw prompt / output storage

The SDK does not store raw prompts or raw outputs by default — only fingerprints and the redacted-input field. If you turn on raw retention via an option that your application maintains (e.g., storing the prompt blob in a sibling object), VouchRail's redaction does not reach it. That blob is your responsibility to keep PII-clean.

A common pitfall: applications log the full prompt to their *own* observability stack (Langfuse, Datadog) and assume the audit chain inherits that log's PII story. It does not. Treat each retention store independently for PII review.

## See also

- [PII redaction — patterns, custom regex, ReDoS notes](./pii-redaction.md)
- [Threat model](./threat-model.md)
- [Storage hardening — token-store backups](./storage-hardening.md)
- [Known limitations §8](../legal/limitations.md#8-article-12--gdpr-resolution-is-a-pattern-not-a-guarantee)
