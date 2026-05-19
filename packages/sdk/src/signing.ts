import { createHmac } from 'node:crypto';

import type { SigningKeyConfig } from './config.js';

export interface Signer {
  /** Returns a signature string for the given SHA-256 hex digest. */
  sign(entryHashHex: string): Promise<string>;
  /** Identifier of the key used; recorded in the signature metadata if needed. */
  readonly keyId: string;
}

export class InlineSigner implements Signer {
  readonly keyId = 'inline';
  constructor(private readonly secret: string) {
    if (!secret || secret.length < 16) {
      // Phase 1: refuse very short secrets so that we don't ship signatures
      // that are trivially forgeable. The spec strongly recommends KMS.
      throw new Error(
        'InlineSigner: secret must be at least 16 characters. ' +
          'Inline signing is intended for development only; use a KMS signer in production.',
      );
    }
  }

  async sign(entryHashHex: string): Promise<string> {
    const mac = createHmac('sha256', this.secret).update(entryHashHex, 'utf8').digest('hex');
    return `hmac-sha256:${this.keyId}:${mac}`;
  }
}

class ExternalSigner implements Signer {
  constructor(
    readonly keyId: string,
    private readonly signFn: (entryHashHex: string) => Promise<string> | string,
  ) {}

  async sign(entryHashHex: string): Promise<string> {
    const out = await this.signFn(entryHashHex);
    if (typeof out !== 'string' || out.length === 0) {
      throw new Error('External signer returned an invalid signature');
    }
    return out;
  }
}

export function createSigner(config: SigningKeyConfig): Signer {
  switch (config.kind) {
    case 'inline':
      return new InlineSigner(config.secret);
    case 'kms':
      return new ExternalSigner(config.keyId, config.sign);
    default: {
      const _exhaustive: never = config;
      void _exhaustive;
      throw new Error('createSigner: unknown signing key kind');
    }
  }
}
