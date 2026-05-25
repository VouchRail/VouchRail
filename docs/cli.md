# CLI usage

The `vouchrail` command-line tool ships in both TypeScript (`@vouchrail/cli`) and Python (`vouchrail` PyPI package). Both produce identical output for the same chain.

## Install

```bash
# TypeScript — one-shot
pnpm dlx @vouchrail/cli --help

# TypeScript — installed
pnpm add -D @vouchrail/cli
pnpm exec vouchrail --help

# Python
pip install vouchrail
vouchrail --help
```

## Config discovery

Without `--config`, the CLI looks in the current directory for:

1. `vouchrail.config.json`
2. `.vouchrail.json` (fallback)

Schema is described in [Configuration reference](./configuration.md#json-config-file-vouchrailconfigjson). All fields can be overridden by command-line flags:

```
--config <path>          # explicit config file location
--system-id <id>         # override config.systemId
--storage-dir <dir>      # override to local backend pointed at <dir>
--s3-bucket <bucket>     # override to S3 backend
--s3-region <region>
--s3-prefix <prefix>
--json                   # machine-readable output (where supported)
```

## `init`

Writes a starter config file.

```bash
vouchrail init                          # writes vouchrail.config.json
vouchrail init --output config.json     # custom path
vouchrail init --force                  # overwrite existing
```

Exit codes: `0` written; `2` refused to overwrite (without `--force`).

## `query`

Retrieve all entries for a single case.

```bash
vouchrail query --case-id candidate-12345
vouchrail query --case-id candidate-12345 --from 2026-08-01T00:00:00Z --to 2026-09-01T00:00:00Z
vouchrail query --case-id candidate-12345 --json
```

Default output (one entry per line, terse):

```
2026-05-19T12:00:00.000Z 00000000 case=candidate-12345 model=anthropic/claude-3-5-sonnet@20241022 reasons=OK review=approve
```

`--json` switches to one JSON object per line (the full entry).

Exit codes: `0` ok; `2` missing/invalid `--case-id` or bad `--from`/`--to`.

## `verify`

Walk the configured range and recompute the hash chain. **Offline. No VouchRail cloud required.**

```bash
vouchrail verify                                            # all entries
vouchrail verify --from 2026-08-01T00:00:00Z --to ...        # date range
vouchrail verify --case-id candidate-12345                   # one case
vouchrail verify --json                                      # machine-readable
vouchrail verify --report report.json                        # write a verification report
vouchrail verify --report report.md                          # ditto, Markdown
```

Clean chain:

```
✔ Chain valid. 42 entries verified.
```

Tampered chain:

```
✘ Chain INVALID at index 17.
  reason: entry_hash_mismatch
  detail: entry at index 17 (callId=…) has been modified
```

`--json` form:

```json
{
  "systemId": "hireflow-resume-screener",
  "entriesChecked": 42,
  "result": { "valid": true }
}
```

### Verification reports

`--report <path>` writes a structured report alongside the normal output. The extension picks the format:

- `*.json` — machine-readable, the same shape consumers feed into compliance dashboards.
- `*.md` — human-readable, the same shape you paste into a buyer's evidence packet.

JSON report (abridged):

```json
{
  "systemId": "hireflow-resume-screener",
  "range": { "from": null, "to": null, "caseId": null },
  "entriesVerified": 42,
  "firstSequence": 0,
  "lastSequence": 41,
  "firstEntryHash": "…",
  "lastEntryHash": "…",
  "firstStartedAt": "2026-05-01T00:00:00.000Z",
  "lastEndedAt": "2026-05-25T11:59:30.123Z",
  "chain": { "valid": true },
  "signatureCheck": {
    "method": "not-performed",
    "note": "Signature verification requires environment-specific key material; this CLI verifies chain integrity only."
  },
  "generatedAt": "2026-05-25T12:00:00.000Z",
  "cliVersion": "0.1.0"
}
```

Notes:

- `firstSequence` / `lastSequence` are 0-based positions within the verified slice, not absolute chain offsets. Filtering with `--from` / `--to` / `--case-id` narrows the slice.
- Signature verification is not part of the chain walk — KMS-signed chains need environment-specific verification (see [Signing keys](./signing-keys.md)). The report records that it was not performed; it does not claim signatures are valid.
- On a tampered chain, `chain.valid` is `false` and the report records `brokenAt`, `reason`, and `detail` (matching the stdout output).

Exit codes: `0` valid; `1` invalid.

## `anchor`

Emit a chain-head anchor: the last sequence number, the last entry hash, and the last entry's signature. Stash this file outside the trust boundary that holds the audit logs; a future rewrite of the chain must also rewrite every anchor wherever you stashed them, which is the detectable part.

```bash
vouchrail anchor                                            # stdout
vouchrail anchor --output chain-head.json                   # file
```

Output:

```json
{
  "systemId": "hireflow-resume-screener",
  "sequence": 1234,
  "entryCount": 1235,
  "recordHash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "algorithm": "sha256",
  "signature": "hmac-sha256:inline:…",
  "anchoredAt": "2026-05-25T12:00:00.000Z",
  "cliVersion": "0.1.0"
}
```

Notes:

- The anchor reads the full chain for the configured `systemId`. Range filters are intentionally not supported — an anchor of a slice is a confusing artifact.
- The anchor proves "the chain reached state X by the time the file was written". It does not timestamp; pin the anchor in a system whose timestamp you can later prove independently (e.g., a Git commit signed by a key under a different custody chain).
- See [Threat model — chain-head anchoring](./threat-model.md#chain-head-anchoring) for the threat scenarios this defends and what it does not.

Exit codes: `0` written; `2` no entries found for the system id.

## `export`

Emit a JSONL evidence bundle. Either a single case OR a date range is required.

```bash
vouchrail export --case-id candidate-12345 --output bundle.jsonl
vouchrail export --case-id candidate-12345                      # stdout
vouchrail export --from 2026-08-01T00:00:00Z --to 2026-08-31T23:59:59Z --output august.jsonl
```

Exit codes: `0` ok; `1` write failure (e.g., disk full); `2` no filters supplied.

## End-to-end smoke check

```bash
export AUDIT_SIGNING_KEY=a-secret-that-is-long-enough-1234567890
pnpm example:resume                             # writes ./examples/resume-screening/audit-logs
vouchrail verify --storage-dir ./examples/resume-screening/audit-logs \
                 --system-id resume-screener-example
```

You should see `✔ Chain valid.` printed. Tamper one byte in the JSONL and re-run to see the chain break.

## Verifying S3-stored chains offline

```bash
aws s3 sync s3://hireflow-audit-logs/prod/<systemId> ./local-copy
vouchrail verify --storage-dir ./local-copy --system-id <systemId>
```

Pulling the bytes locally keeps verification fully air-gapped from the SDK's hosted services (we don't have any) and from VouchRail itself.
