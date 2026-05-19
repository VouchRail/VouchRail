# @auditlayer/cli

Command-line tool for the AuditLayer audit log. Used by engineers and
compliance officers to:

- `init` — write a starter configuration file
- `query` — retrieve all entries for a case
- `verify` — recompute the hash chain and report tamper events
- `export` — emit a JSONL evidence bundle for a case or date range

**Offline by design.** The `verify` command runs entirely against the
configured storage backend; no AuditLayer cloud connection is required.
This is the property described in spec §13.6.B.

## Install

```bash
pnpm add -D @auditlayer/cli
# or one-shot
pnpm dlx @auditlayer/cli --help
```

## Configuration

By default the CLI reads `./auditlayer.config.json` (override with
`--config <path>`). Example:

```json
{
  "systemId": "hireflow-resume-screener",
  "storage": { "type": "local", "dir": "./audit-logs" }
}
```

For S3:

```json
{
  "systemId": "hireflow-resume-screener",
  "storage": { "type": "s3", "bucket": "hireflow-audit-logs", "region": "eu-west-1" }
}
```

## Commands

```text
auditlayer init [--output auditlayer.config.json]
auditlayer query --case-id <id> [--from <iso>] [--to <iso>]
auditlayer verify [--from <iso>] [--to <iso>] [--case-id <id>]
auditlayer export --case-id <id> [--output <path>]
auditlayer export --from <iso> --to <iso> [--output <path>]
```

Global flags:

- `--config <path>` — config file location
- `--system-id <id>` — override systemId
- `--storage-dir <dir>` — override local storage dir
- `--s3-bucket <bucket>` / `--s3-region <region>` / `--s3-prefix <p>` — override S3
- `--json` — emit machine-readable output

## License

Apache-2.0. See repository root [`LICENSE`](../../LICENSE).
