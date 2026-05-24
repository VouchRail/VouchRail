# Example — AI credit decision (fintech, EU AI Act Annex III)

AI-assisted creditworthiness assessment is explicitly listed in Annex III
of the EU AI Act as a high-risk application. This example demonstrates
VouchRail recording every credit decision, with an explicit
**`humanReview`** step for borderline cases — exactly the kind of
human-oversight artifact Article 14 expects.

## Run

```bash
pnpm install
pnpm example:credit
```

## What the example demonstrates

- Manual `startCall` / `endCall` integration (no SDK wrap), useful for
  decision pipelines that don't go through a single LLM call.
- `reasonCodes` on every decision — machine-readable explanation.
- `humanReview` records when the decision is escalated to a credit
  officer and either approved, overridden, or escalated further.
- `outputDecision` fully structured (limit, term, APR), enabling
  reconstruction during a regulator audit.

## Verify

```bash
pnpm dlx @vouchrail/cli verify \
  --system-id credit-decision-example \
  --storage-dir ./audit-logs
```
