# Example — AI healthcare triage (Annex III high-risk)

AI triage / pre-screening systems (non-medical-device classification) fall
under EU AI Act Annex III. This example shows AuditLayer recording every
triage recommendation with:

- Full PII pseudonymization (patient identifiers tokenized at log time;
  reveal-on-justified-request via the token store).
- `referenceDatabase` field per Article 12(3)(b) — recording which
  knowledge base was queried.
- Risk flags when the model's confidence is low.

## Run

```bash
pnpm install
pnpm example:health
```

## Verify

```bash
pnpm dlx @auditlayer/cli verify \
  --system-id healthcare-triage-example \
  --storage-dir ./audit-logs
```
