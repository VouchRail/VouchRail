# auditlayer (Python)

Python SDK for **AuditLayer** — EU AI Act Article 12 tamper-evident audit logs.

Cross-language hash compatibility: a TypeScript service and a Python service can
interleave entries in the same hash chain, and either CLI verifies the result
with byte-identical SHA-256 output.

## Status

**Tier S scaffold** (per `dev_docs/auditlayer framework expansion.md`). The
schema package (JCS canonicalization, SHA-256 hash chain, Pydantic models) is
implemented and conforms to the TypeScript reference implementation. Storage,
signer, PII redactor, provider wrappers, and CLI parity ship on the roadmap
below.

## Roadmap

| Tier | Item                                           | Status      |
| ---- | ---------------------------------------------- | ----------- |
| S1   | Conformance vector test suite (cross-language) | In progress |
| S2   | Python schema package (`auditlayer.schema`)    | Done        |
| S3   | Python core SDK (AuditLogger, storage, signer) | Planned     |
| S4   | Python wrap for Anthropic (sync + async)       | Planned     |
| S5   | Python wrap for OpenAI (sync + async)          | Planned     |
| S6   | Python CLI parity                              | Planned     |
| S7   | Python examples (3 examples mirroring TS)      | Planned     |
| S8   | PyPI publication                               | Planned     |

## Install

```bash
uv pip install -e .[dev]
# or
pip install -e .[dev]
```

## Hash compatibility invariant

For any identical logical input, TypeScript SDK and Python SDK MUST produce
byte-identical:

1. JCS canonical serialization output (RFC 8785)
2. Entry hash (SHA-256 of canonical form)
3. Hash chain progression

The conformance test suite lives at the repo root under `conformance-vectors/`.
Both SDKs run the same vectors on every CI build.

## License

Apache-2.0
