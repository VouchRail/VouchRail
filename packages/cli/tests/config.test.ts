import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { loadConfig, resolveConfig } from '../src/config.js';

describe('config', () => {
  let cwd: string;
  let prevCwd: string;

  beforeEach(() => {
    cwd = mkdtempSync(join(tmpdir(), 'auditlayer-cfg-'));
    prevCwd = process.cwd();
    process.chdir(cwd);
  });
  afterEach(() => {
    process.chdir(prevCwd);
    rmSync(cwd, { recursive: true, force: true });
  });

  it('loadConfig returns null when no config exists', async () => {
    const c = await loadConfig();
    expect(c).toBeNull();
  });

  it('loadConfig reads a valid local config', async () => {
    writeFileSync(
      join(cwd, 'auditlayer.config.json'),
      JSON.stringify({ systemId: 'x', storage: { type: 'local', dir: './logs' } }),
    );
    const c = await loadConfig();
    expect(c?.systemId).toBe('x');
    expect(c?.storage.type).toBe('local');
  });

  it('loadConfig rejects malformed configs', async () => {
    writeFileSync(join(cwd, 'auditlayer.config.json'), '{}');
    await expect(loadConfig()).rejects.toThrow(/systemId/);
  });

  it('loadConfig rejects --config paths containing ".." segments', async () => {
    await expect(loadConfig('../etc/passwd')).rejects.toThrow(/'\.\.'/);
  });

  it('resolveConfig requires systemId', () => {
    expect(() => resolveConfig(null, {})).toThrow(/systemId/);
  });

  it('resolveConfig requires a storage source', () => {
    expect(() => resolveConfig(null, { systemId: 'x' })).toThrow(/storage/);
  });

  it('CLI overrides take precedence', () => {
    const c = resolveConfig(
      { systemId: 'config-id', storage: { type: 'local', dir: '/orig' } },
      { systemId: 'cli-id', storageDir: '/cli' },
    );
    expect(c.systemId).toBe('cli-id');
    expect(c.storage).toEqual({ type: 'local', dir: '/cli' });
  });

  it('S3 overrides build an s3 storage record', () => {
    const c = resolveConfig(null, {
      systemId: 'sys',
      s3Bucket: 'b',
      s3Region: 'eu-west-1',
      s3Prefix: 'p',
    });
    expect(c.storage).toEqual({ type: 's3', bucket: 'b', region: 'eu-west-1', prefix: 'p' });
  });
});
