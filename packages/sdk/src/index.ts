export { AuditLogger } from './audit-logger.js';
export { SDK_NAME, SDK_VERSION } from './version.js';

export type {
  AuditLoggerConfig,
  StorageConfig,
  LocalStorageConfig,
  S3StorageConfig,
  RetentionConfig,
  HashChainConfig,
  SigningKeyConfig,
  InlineSigningKeyConfig,
  KmsSigningKeyConfig,
  PiiRedactionConfig,
  PiiTokenStoreConfig,
  WrapContext,
  StartCallInput,
  EndCallInput,
} from './config.js';

export type { StorageBackend } from './backends/types.js';
export { LocalStorageBackend } from './backends/local.js';
export { S3StorageBackend } from './backends/s3.js';

export type { PiiTokenStore } from './pii.js';
export {
  DEFAULT_PII_PATTERNS,
  detectPii,
  hashString,
  InMemoryPiiTokenStore,
  PiiRedactor,
  SqlitePiiTokenStore,
} from './pii.js';

export type { Signer } from './signing.js';
export { createSigner, InlineSigner } from './signing.js';

export { fingerprint, deriveDurationMs, nowIso, uuidv4 } from './util.js';
