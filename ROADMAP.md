# Roadmap

What's in flight, what's queued, what's deferred. Updated as items land.

This file is intentionally short. Anything not listed here is not committed.

## Now

Targeted at the `v0.1.0-alpha` cut.

- Stabilize SDK surface — minor type / signature changes still possible before `v1.0`
- Verification reports (`vouchrail verify --report report.{json,md}`) for compliance/buyer-facing output
- Chain-head anchoring (`vouchrail anchor`) — minimal external pin file
- Quickstart polish: every command in README runs from a fresh clone
- Example demos that run without a paid API key
- Cross-language conformance hardening — every new schema field gets a vector

## Next

Likely landing before `v0.2`.

- LangChain callback handler (TypeScript + Python)
- LangGraph node wrapper
- S3 Object Lock setup guide with Terraform / CloudFormation snippets
- Python S3 backend parity (currently TS-only)
- `vouchrail anchor verify` — given two anchor files from different times, prove the chain extended monotonically
- npm + PyPI alpha publishes (install commands in README become real)
- Pre-built KMS signer adapters (AWS, GCP, Vault)

## Later

Deferred — interesting, not committed.

- Hosted dashboard (signature verification, anchor monitoring, retention warnings)
- ML-based PII detection (replaces / augments regex)
- External transparency log integration
- Multi-tenant policy controls
- SOC 2 readiness
- Notified Body conformity assessment process
- Replication-aware backends (S3 cross-region, dual-cloud)

## Out of scope

Things VouchRail intentionally does NOT chase:

- A SaaS that hosts customer audit logs. Customer-owned storage is a load-bearing piece of the threat model — see [docs/threat-model.md](./docs/threat-model.md).
- Legal certification of compliance. Infrastructure does not certify; auditors do.
- A regulator-ready guarantee. The infrastructure is regulator-friendly; the deployment is the customer's responsibility.

## Contributing to the roadmap

Propose a change via a GitHub issue tagged `roadmap`. PRs that implement a listed item are welcome; PRs that add unlisted features are also welcome but need a brief design note explaining what the item does and why it fits the project.
