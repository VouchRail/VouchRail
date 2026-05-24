/**
 * VouchRail typed error hierarchy.
 *
 * Every public failure path throws one of these. Tests and callers should
 * branch on `instanceof` or `error.code`, never on `error.message` text.
 *
 * Adding a new error class: subclass `VouchRailError`, assign a stable
 * `code`, and register it in `ERROR_CODES`.
 */

export const ERROR_CODES = {
  // Configuration
  CONFIG_INVALID: 'VOUCHRAIL_CONFIG_INVALID',
  CONFIG_MISSING_FIELD: 'VOUCHRAIL_CONFIG_MISSING_FIELD',
  CONFIG_UNKNOWN_BACKEND: 'VOUCHRAIL_CONFIG_UNKNOWN_BACKEND',
  CONFIG_UNKNOWN_STORE: 'VOUCHRAIL_CONFIG_UNKNOWN_STORE',

  // Storage
  STORAGE_BAD_JSON: 'VOUCHRAIL_STORAGE_BAD_JSON',
  STORAGE_BAD_SCHEMA: 'VOUCHRAIL_STORAGE_BAD_SCHEMA',
  STORAGE_BACKEND_MISSING_DEP: 'VOUCHRAIL_STORAGE_BACKEND_MISSING_DEP',

  // Schema / hashing
  SCHEMA_HASH_RECHECK_FAILED: 'VOUCHRAIL_SCHEMA_HASH_RECHECK_FAILED',
  SCHEMA_INVALID_TIMESTAMP: 'VOUCHRAIL_SCHEMA_INVALID_TIMESTAMP',

  // Signing
  SIGNER_INVALID_SECRET: 'VOUCHRAIL_SIGNER_INVALID_SECRET',
  SIGNER_EXTERNAL_INVALID_OUTPUT: 'VOUCHRAIL_SIGNER_EXTERNAL_INVALID_OUTPUT',

  // Provider
  PROVIDER_UNSUPPORTED_CLIENT: 'VOUCHRAIL_PROVIDER_UNSUPPORTED_CLIENT',

  // PII
  PII_TOKEN_STORE_MISSING: 'VOUCHRAIL_PII_TOKEN_STORE_MISSING',
  PII_TOKEN_STORE_MISSING_DEP: 'VOUCHRAIL_PII_TOKEN_STORE_MISSING_DEP',

  // Logger lifecycle
  LOGGER_CALL_NOT_PENDING: 'VOUCHRAIL_LOGGER_CALL_NOT_PENDING',
  LOGGER_PATH_SEGMENT_UNSAFE: 'VOUCHRAIL_LOGGER_PATH_SEGMENT_UNSAFE',
} as const;

export type VouchRailErrorCode = (typeof ERROR_CODES)[keyof typeof ERROR_CODES];

export class VouchRailError extends Error {
  readonly code: VouchRailErrorCode;
  readonly context: Readonly<Record<string, unknown>>;

  constructor(code: VouchRailErrorCode, message: string, context: Record<string, unknown> = {}) {
    super(message);
    this.name = new.target.name;
    this.code = code;
    this.context = Object.freeze({ ...context });
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class VouchRailConfigError extends VouchRailError {}
export class VouchRailStorageError extends VouchRailError {}
export class VouchRailSchemaError extends VouchRailError {}
export class VouchRailSignerError extends VouchRailError {}
export class VouchRailProviderError extends VouchRailError {}
export class VouchRailPiiError extends VouchRailError {}
/** Logger lifecycle / state-machine violations (e.g. endCall on a finalized callId). */
export class VouchRailLifecycleError extends VouchRailError {}
