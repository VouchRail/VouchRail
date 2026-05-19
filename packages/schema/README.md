# @auditlayer/schema

The schema, runtime validators, canonical serialization, and SHA-256
hash-chain helpers shared by `@auditlayer/sdk` and `@auditlayer/cli`.

Designed to support **EU AI Act Article 12** record-keeping for high-risk
AI systems.

## What this package provides

- **`AuditLogEntry`** — TypeScript type describing one structured audit
  log entry, mapped field-by-field to Article 12 paragraphs.
- **`AuditLogEntrySchema`** — a Zod runtime validator for the same.
- **`canonicalize`** — RFC 8785 JSON Canonicalization Scheme (JCS)
  serialization (deterministic UTF-8 NFC, sorted keys, canonical numeric
  representation). Required so that two parties that compute the hash of
  the same entry get the same hash.
- **Hash chain helpers** — `computeEntryHash`, `linkEntry`, `verifyChain`.

## Install

```bash
pnpm add @auditlayer/schema
```

## Example

```ts
import {
  AuditLogEntrySchema,
  canonicalize,
  computeEntryHash,
  linkEntry,
  verifyChain,
} from '@auditlayer/schema';

const entry = AuditLogEntrySchema.parse({
  /* … your fields … */
});

const canonical = canonicalize(entry);
const hash = computeEntryHash(entry);

const linked = linkEntry(entry, previousEntry);
const result = verifyChain([entry, linked]);
if (!result.valid) {
  console.error('Chain broken at index', result.brokenAt);
}
```

## Versioning

The `schemaVersion` field on every entry is the source of truth. We do not
silently break the schema; any breaking field change requires a new
`schemaVersion` value (e.g., `auditlayer-v1.0` → `auditlayer-v2.0`) and a
migration note.

## License

Apache-2.0. See repository root [`LICENSE`](../../LICENSE).
