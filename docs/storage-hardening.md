# Storage hardening

The hash chain proves nobody altered records that still exist. Real evidentiary strength also requires that records cannot be silently *removed*. That property lives in the storage layer, not the SDK.

This page covers production-grade storage configuration for the two shipped backends. For the API surface, see [Storage backends](./storage-backends.md).

## Posture summary

| Backend          | Suitable for                    | Tamper-evident? | Tamper-resistant? |
| ---------------- | ------------------------------- | --------------- | ----------------- |
| Local filesystem | Dev, demos, single-host on-prem | Yes             | No (delete-able)  |
| AWS S3           | Production                      | Yes             | Yes (with Object Lock) |
| Custom backend   | Whatever you implement          | Yes             | Depends on you    |

Tamper-evidence is given by VouchRail itself — every backend stores the same hash-chained bytes. Tamper-resistance (preventing deletion / overwrite) is a storage-layer property the operator must configure.

## Local disk

For development only. Threat profile:

- Any process with write access to the directory can delete files.
- File modification times are not authoritative — `mtime` and `atime` are operator-controllable.
- Filesystem snapshots are not a substitute for WORM. A privileged user can roll back a snapshot to a state without the record.

If you ship a workload on local disk in production, you have not built an audit log. You have built a structured log that *could* be made into one given storage that the application cannot reach.

## AWS S3 production checklist

Configure these on the bucket before the application ever writes to it.

### Bucket settings

| Setting                       | Value                                                              | Rationale                                                   |
| ----------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------- |
| Object Lock                   | Enabled at bucket creation (cannot be retrofitted)                 | WORM enforcement                                            |
| Object Lock mode              | `COMPLIANCE`                                                       | No bypass, even by root. `GOVERNANCE` allows privileged delete — too weak |
| Default retention             | ≥ your regulatory minimum (EU AI Act deployer baseline: 6 months)  | Catches writers that forget per-object retention            |
| Versioning                    | Enabled                                                            | Object Lock requires versioning                             |
| Default encryption            | SSE-KMS with a customer-managed key                                | Allows independent key access control                       |
| Block all public access       | All four toggles ON                                                | Defense in depth                                            |
| Bucket policy: deny deletes   | `s3:DeleteObject` / `s3:DeleteObjectVersion` denied for all principals (Object Lock enforces; this is belt-and-braces) | Reduce blast radius of leaked Object-Lock-aware credentials |
| Lifecycle                     | Transition to `GLACIER_IR` after retention floor (optional)         | Storage-cost optimization without losing immutability       |
| MFA Delete                    | Enabled on the bucket root                                          | Last resort against complete bucket deletion                |
| Inventory                     | Daily inventory delivered to a separate audit account               | Independent record of what existed when                     |

### IAM separation

Three roles, never combined:

1. **Application role** (the agent service)
   - `s3:PutObject` on the audit prefix.
   - `s3:GetObject` on the audit prefix (only if your app needs to read its own logs).
   - `kms:Sign` on the signer KMS key.
   - No `s3:DeleteObject`, no `kms:GetPublicKey`, no `kms:Decrypt`.
2. **Verifier role** (cron job, oncall human, regulator-export tool)
   - `s3:GetObject` + `s3:ListBucket` on the audit prefix.
   - `kms:Verify` if you verify signatures against KMS public material.
   - No write.
3. **Bucket admin role** (rare, change-controlled)
   - `s3:PutBucketPolicy`, `s3:PutBucketObjectLockConfiguration`.
   - Held by a different human than the application maintainer; ideally requires a change-ticket reference.

### KMS configuration

- One CMK for at-rest encryption (used by the bucket default encryption).
- A separate CMK for signing (`signingKey.kind: 'kms'` in the SDK). Compromise of the encryption key does not let an attacker forge signatures.
- Key policy grants `kms:Sign` to the application role; `kms:Decrypt` / `kms:GenerateDataKey` to the encryption role (often the bucket itself via SSE-KMS); `kms:CreateKey` / `kms:ScheduleKeyDeletion` to a key-admin role on a separate human.
- Schedule key rotation; the `signature` field's key id makes the rotation reversible at verify-time.

### SDK config that matches

```ts
storage: {
  type: 's3',
  bucket: 'hireflow-audit-logs',
  region: 'eu-west-1',
  prefix: 'production',
  workMode: true,
  kmsKeyId: 'arn:aws:kms:eu-west-1:123:key/encryption-cmk',
},
signingKey: {
  kind: 'kms',
  keyId: 'arn:aws:kms:eu-west-1:123:key/signing-cmk',
  sign: async (hex) => { /* KMS Sign call */ },
},
```

Pass `kmsKeyId` even when the bucket default already covers it — drift detection at write time beats discovery during incident response.

## S3-compatible backends (MinIO, R2, etc.)

The `endpoint` option lets you point at any S3-compatible service. Caveats:

- **Object Lock parity.** Cloudflare R2 does not support Object Lock at time of writing. MinIO supports it but the operator runs the cluster, so trust devolves to whoever runs MinIO. Treat these as "tamper-evident, not tamper-resistant" unless you specifically verified WORM enforcement end-to-end.
- **Checksums.** VouchRail always sends `ChecksumAlgorithm: SHA256` on PUT. Confirm the backend validates it; some S3-compatible services silently drop unsupported headers.
- **Versioning.** Required for Object Lock. Confirm versioning is on before relying on retention.

## Periodic verification

The cheapest non-trivial control: scheduled `vouchrail verify` over the live store with alerting on non-zero exit. Recommended cadence:

- Hourly for high-volume production. The chain validates from genesis in seconds for chains under tens of thousands of entries.
- Daily for low-volume systems.
- Once on every CI build that touches anything in the audit pipeline.

Combine with [chain-head anchoring](./threat-model.md#chain-head-anchoring): the verification run also produces an anchor JSON checked into a Git repo (or piped to a webhook), giving you a third-party-verifiable record of "the chain reached state X by time T".

## Backup strategy

The chain is internally redundant — verifying any contiguous subrange detects corruption — but it's not redundant across copies. Three rules:

1. **Backups are append-only.** Replicate forward in time; never overwrite older backups with newer ones. A backup that lets you restore over current data lets a compromised admin "restore" a rewritten history.
2. **Backups include the genesis block.** The first entry of the chain anchors verification. A backup that starts mid-chain still verifies, but you can no longer prove that no entries existed before the backup start.
3. **Backups verify on restore.** Run `vouchrail verify` against any restored snapshot before trusting it. A backup that hasn't been verification-tested is not yet a backup.

For S3 specifically: cross-region replication into a bucket in a separate AWS account with its own Object Lock is the strong default. The application role does not hold credentials for the destination.

## What this does NOT give you

- A guarantee that any *specific* regulator accepts the configuration. Refer to [legal/limitations.md](../legal/limitations.md).
- Defense against an attacker who controls both the application role and the bucket-admin role. That's the separation-of-duties premise — break it and the controls collapse.
- Eternal storage. Retention is bounded by your configuration; objects can be deleted *after* their retention window expires. If you need indefinite retention, set retention longer than you expect to need.
