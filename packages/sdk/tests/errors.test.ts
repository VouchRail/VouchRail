import { describe, expect, it } from 'vitest';

import {
  VouchRailConfigError,
  VouchRailError,
  VouchRailPiiError,
  VouchRailProviderError,
  VouchRailSchemaError,
  VouchRailSignerError,
  VouchRailStorageError,
  ERROR_CODES,
} from '../src/errors.js';

describe('VouchRailError', () => {
  it('carries code + immutable context', () => {
    const err = new VouchRailConfigError(ERROR_CODES.CONFIG_INVALID, 'msg', { foo: 'bar' });
    expect(err).toBeInstanceOf(Error);
    expect(err).toBeInstanceOf(VouchRailError);
    expect(err).toBeInstanceOf(VouchRailConfigError);
    expect(err.code).toBe(ERROR_CODES.CONFIG_INVALID);
    expect(err.context).toEqual({ foo: 'bar' });
    expect(Object.isFrozen(err.context)).toBe(true);
  });

  it('subclasses do not collide', () => {
    const cfg = new VouchRailConfigError(ERROR_CODES.CONFIG_INVALID, 'm');
    const store = new VouchRailStorageError(ERROR_CODES.STORAGE_BAD_JSON, 'm');
    const schema = new VouchRailSchemaError(ERROR_CODES.SCHEMA_HASH_RECHECK_FAILED, 'm');
    const signer = new VouchRailSignerError(ERROR_CODES.SIGNER_INVALID_SECRET, 'm');
    const provider = new VouchRailProviderError(ERROR_CODES.PROVIDER_UNSUPPORTED_CLIENT, 'm');
    const pii = new VouchRailPiiError(ERROR_CODES.PII_TOKEN_STORE_MISSING, 'm');
    expect(cfg).not.toBeInstanceOf(VouchRailStorageError);
    expect(store).not.toBeInstanceOf(VouchRailConfigError);
    expect(schema).not.toBeInstanceOf(VouchRailSignerError);
    expect(signer).not.toBeInstanceOf(VouchRailProviderError);
    expect(provider).not.toBeInstanceOf(VouchRailPiiError);
    expect(pii).not.toBeInstanceOf(VouchRailSchemaError);
  });

  it('all codes are stable strings (no collisions, no empties)', () => {
    const values = Object.values(ERROR_CODES);
    const set = new Set(values);
    expect(set.size).toBe(values.length);
    for (const v of values) {
      expect(typeof v).toBe('string');
      expect(v.length).toBeGreaterThan(0);
      expect(v.startsWith('VOUCHRAIL_')).toBe(true);
    }
  });

  it('error name matches its class', () => {
    expect(new VouchRailConfigError(ERROR_CODES.CONFIG_INVALID, 'x').name).toBe(
      'VouchRailConfigError',
    );
    expect(new VouchRailStorageError(ERROR_CODES.STORAGE_BAD_JSON, 'x').name).toBe(
      'VouchRailStorageError',
    );
  });
});
