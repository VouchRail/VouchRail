import { describe, expect, it } from 'vitest';

import { InlineSigner, createSigner } from '../src/signing.js';

describe('InlineSigner', () => {
  it('produces a deterministic HMAC-SHA256 signature for the same input', async () => {
    const a = new InlineSigner('a-secret-that-is-long-enough-1234567890');
    const b = new InlineSigner('a-secret-that-is-long-enough-1234567890');
    const sigA = await a.sign('deadbeef');
    const sigB = await b.sign('deadbeef');
    expect(sigA).toBe(sigB);
    expect(sigA).toMatch(/^hmac-sha256:inline:[0-9a-f]{64}$/);
  });

  it('different secrets produce different signatures', async () => {
    const a = new InlineSigner('secret-one-that-is-long-enough-1234567890');
    const b = new InlineSigner('secret-two-that-is-long-enough-1234567890');
    const sigA = await a.sign('deadbeef');
    const sigB = await b.sign('deadbeef');
    expect(sigA).not.toBe(sigB);
  });

  it('refuses very short secrets', () => {
    expect(() => new InlineSigner('short')).toThrow(/16/);
  });
});

describe('createSigner', () => {
  it('creates an inline signer from inline config', async () => {
    const s = createSigner({
      kind: 'inline',
      secret: 'abcdefghij1234567890',
    });
    expect(await s.sign('aa')).toMatch(/^hmac-sha256:inline:/);
  });

  it('creates a KMS-pluggable signer that calls the provided function', async () => {
    let captured = '';
    const s = createSigner({
      kind: 'kms',
      keyId: 'kms-key-1',
      sign: (h) => {
        captured = h;
        return `signed:${h}`;
      },
    });
    expect(s.keyId).toBe('kms-key-1');
    expect(await s.sign('deadbeef')).toBe('signed:deadbeef');
    expect(captured).toBe('deadbeef');
  });

  it('rejects empty signature returned from external signer', async () => {
    const s = createSigner({
      kind: 'kms',
      keyId: 'kms-key-1',
      sign: () => '',
    });
    await expect(s.sign('aa')).rejects.toThrow(/invalid signature/);
  });
});
