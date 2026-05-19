# Example — AI resume screening (HR tech, EU AI Act Annex III)

A worked demo of AuditLayer for **AI-assisted recruitment**, which is the
single largest Annex III high-risk category under the EU AI Act.

The example does not call a real LLM — it ships with a mock provider so
you can run it offline. Replace the mock with `@anthropic-ai/sdk` or
`openai` to wire it up to a real provider; the `audit.wrap()` call stays
identical.

## Run

```bash
pnpm install
pnpm example:resume
```

## What the example demonstrates

- One config-line integration of AuditLayer with an Anthropic-style client.
- Article 12 fields recorded for every candidate decision:
  `caseId` (candidate ID), `promptTemplateId` + version, model + version,
  prompt + input + output fingerprints, `outputDecision`, `reasonCodes`,
  `operatorId`, optional `humanReview`.
- PII pseudonymization: candidate names, emails, and phones in the input
  are replaced with `pii:` tokens at log time.
- Hash chain is built across multiple decisions; `auditlayer verify`
  detects any modification.

## Verify the resulting logs

```bash
pnpm dlx @auditlayer/cli verify \
  --system-id resume-screener-example \
  --storage-dir ./audit-logs
```
