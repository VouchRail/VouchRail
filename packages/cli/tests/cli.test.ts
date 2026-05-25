import { mkdtempSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { PassThrough } from 'node:stream';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { AuditLogger } from '@vouchrail/sdk';

import {
  anchorCommand,
  exportCommand,
  initCommand,
  queryCommand,
  verifyCommand,
} from '../src/commands.js';
import type { CliConfig } from '../src/config.js';
import { resolveConfig } from '../src/config.js';

const TEST_SECRET = 'test-secret-key-with-enough-length-1234567890';

function captureIO(cwd: string) {
  const stdout = new PassThrough();
  const stderr = new PassThrough();
  const stdoutChunks: Buffer[] = [];
  const stderrChunks: Buffer[] = [];
  stdout.on('data', (b) => stdoutChunks.push(b));
  stderr.on('data', (b) => stderrChunks.push(b));
  return {
    io: { stdout, stderr, cwd },
    out: () => Buffer.concat(stdoutChunks).toString('utf8'),
    err: () => Buffer.concat(stderrChunks).toString('utf8'),
  };
}

async function seedEntries(dir: string, n: number, systemId = 'sys-cli') {
  const audit = new AuditLogger({
    systemId,
    storage: { type: 'local', dir },
    signingKey: { kind: 'inline', secret: TEST_SECRET },
  });
  for (let i = 0; i < n; i++) {
    const id = await audit.startCall({
      caseId: i % 2 === 0 ? 'case-A' : 'case-B',
      modelProvider: 'anthropic',
      modelName: 'claude-3-5-sonnet',
      modelVersion: '20241022',
      promptTemplateId: 'tpl',
      promptTemplateVersion: '1.0.0',
      operatorId: 'op',
      input: { i },
    });
    await audit.endCall(id, { output: { ok: true, i } });
  }
  await audit.close();
}

describe('cli commands', () => {
  let dir: string;
  let cwd: string;
  beforeEach(() => {
    cwd = mkdtempSync(join(tmpdir(), 'vouchrail-cli-'));
    dir = join(cwd, 'audit-logs');
  });
  afterEach(() => {
    rmSync(cwd, { recursive: true, force: true });
  });

  describe('init', () => {
    it('writes a starter config and refuses to overwrite without --force', async () => {
      const a = captureIO(cwd);
      const code1 = await initCommand({}, a.io);
      expect(code1).toBe(0);
      const path = join(cwd, 'vouchrail.config.json');
      expect(existsSync(path)).toBe(true);
      const json = JSON.parse(readFileSync(path, 'utf8'));
      expect(json.systemId).toBe('your-system-id');
      const b = captureIO(cwd);
      const code2 = await initCommand({}, b.io);
      expect(code2).toBe(2);
      expect(b.err()).toMatch(/Refusing to overwrite/);
    });

    it('overwrites with --force', async () => {
      const a = captureIO(cwd);
      await initCommand({}, a.io);
      const b = captureIO(cwd);
      const code = await initCommand({ force: true }, b.io);
      expect(code).toBe(0);
    });
  });

  describe('query', () => {
    it('rejects empty caseId', async () => {
      await seedEntries(dir, 2);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const code = await queryCommand(config, { caseId: '' }, cap.io);
      expect(code).toBe(2);
    });

    it('rejects --from/--to in inverted order', async () => {
      await seedEntries(dir, 2);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      await expect(
        queryCommand(
          config,
          { caseId: 'case-A', from: '2026-12-01T00:00:00.000Z', to: '2026-01-01T00:00:00.000Z' },
          cap.io,
        ),
      ).rejects.toThrow(/must not be after/);
    });

    it('rejects bogus --from', async () => {
      await seedEntries(dir, 2);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      await expect(
        queryCommand(config, { caseId: 'case-A', from: 'notadate' }, cap.io),
      ).rejects.toThrow(/ISO-8601/);
    });

    it('filters by caseId', async () => {
      await seedEntries(dir, 6);
      const config: CliConfig = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const code = await queryCommand(config, { caseId: 'case-A' }, cap.io);
      expect(code).toBe(0);
      const lines = cap.out().trim().split('\n');
      expect(lines).toHaveLength(3);
      expect(cap.err()).toMatch(/Matched 3 entries/);
    });

    it('emits JSON with --json', async () => {
      await seedEntries(dir, 2);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      await queryCommand(config, { caseId: 'case-A', json: true }, cap.io);
      const lines = cap.out().trim().split('\n');
      expect(lines).toHaveLength(1);
      const e = JSON.parse(lines[0]!);
      expect(e.caseId).toBe('case-A');
      expect(e.entryHash).toMatch(/^[0-9a-f]{64}$/);
    });
  });

  describe('verify', () => {
    it('returns 0 and prints OK for a clean chain', async () => {
      await seedEntries(dir, 5);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const code = await verifyCommand(config, {}, cap.io);
      expect(code).toBe(0);
      expect(cap.out()).toMatch(/Chain valid/);
    });

    it('returns 1 and reports tampering when entry is altered on disk', async () => {
      await seedEntries(dir, 5);
      // Tamper with the JSONL on disk.
      const walk = (p: string): string[] => {
        const fs = require('node:fs') as typeof import('node:fs');
        const out: string[] = [];
        for (const item of fs.readdirSync(p)) {
          const next = join(p, item);
          if (fs.statSync(next).isDirectory()) out.push(...walk(next));
          else if (next.endsWith('.jsonl')) out.push(next);
        }
        return out;
      };
      const files = walk(dir).sort();
      const path = files[0]!;
      const lines = readFileSync(path, 'utf8').split('\n').filter(Boolean);
      const e = JSON.parse(lines[0]!);
      e.outputDecision = { tampered: true };
      lines[0] = JSON.stringify(e);
      const fs = require('node:fs') as typeof import('node:fs');
      fs.writeFileSync(path, lines.join('\n') + '\n');

      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const code = await verifyCommand(config, {}, cap.io);
      expect(code).toBe(1);
      expect(cap.out()).toMatch(/Chain INVALID/);
    });

    it('JSON output structure', async () => {
      await seedEntries(dir, 2);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      await verifyCommand(config, { json: true }, cap.io);
      const out = JSON.parse(cap.out().trim());
      expect(out.systemId).toBe('sys-cli');
      expect(out.entriesChecked).toBe(2);
      expect(out.result.valid).toBe(true);
    });
  });

  describe('export', () => {
    it('refuses with no filters', async () => {
      await seedEntries(dir, 1);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const code = await exportCommand(config, {}, cap.io);
      expect(code).toBe(2);
    });

    it('writes JSONL to a file', async () => {
      await seedEntries(dir, 4);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const outFile = join(cwd, 'bundle.jsonl');
      const code = await exportCommand(config, { caseId: 'case-A', output: outFile }, cap.io);
      expect(code).toBe(0);
      const text = readFileSync(outFile, 'utf8').trim();
      expect(text.split('\n')).toHaveLength(2);
    });

    it('writes JSONL to stdout when no --output', async () => {
      await seedEntries(dir, 2);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      await exportCommand(config, { caseId: 'case-A' }, cap.io);
      const lines = cap.out().trim().split('\n');
      expect(lines).toHaveLength(1);
    });
  });

  describe('verify --report', () => {
    it('writes a JSON report next to the chain when --report path.json', async () => {
      await seedEntries(dir, 4);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const reportPath = join(cwd, 'report.json');
      const code = await verifyCommand(config, { report: 'report.json' }, cap.io);
      expect(code).toBe(0);
      const report = JSON.parse(readFileSync(reportPath, 'utf8'));
      expect(report.systemId).toBe('sys-cli');
      expect(report.entriesVerified).toBe(4);
      expect(report.firstSequence).toBe(0);
      expect(report.lastSequence).toBe(3);
      expect(report.firstEntryHash).toMatch(/^[0-9a-f]{64}$/);
      expect(report.lastEntryHash).toMatch(/^[0-9a-f]{64}$/);
      expect(report.chain).toEqual({ valid: true });
      expect(report.signatureCheck.method).toBe('not-performed');
      expect(typeof report.generatedAt).toBe('string');
      expect(typeof report.cliVersion).toBe('string');
      expect(cap.err()).toMatch(/Wrote verification report/);
    });

    it('writes Markdown when --report path.md', async () => {
      await seedEntries(dir, 2);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const reportPath = join(cwd, 'report.md');
      const code = await verifyCommand(config, { report: 'report.md' }, cap.io);
      expect(code).toBe(0);
      const md = readFileSync(reportPath, 'utf8');
      expect(md).toMatch(/^# VouchRail verification report/);
      expect(md).toMatch(/Status\*\*: VALID/);
      expect(md).toMatch(/Entries verified: 2/);
    });

    it('records the broken-link details in the report on a tampered chain', async () => {
      await seedEntries(dir, 3);
      const fs = require('node:fs') as typeof import('node:fs');
      const walk = (p: string): string[] => {
        const out: string[] = [];
        for (const item of fs.readdirSync(p)) {
          const next = join(p, item);
          if (fs.statSync(next).isDirectory()) out.push(...walk(next));
          else if (next.endsWith('.jsonl')) out.push(next);
        }
        return out;
      };
      const path = walk(dir).sort()[0]!;
      const lines = readFileSync(path, 'utf8').split('\n').filter(Boolean);
      const e = JSON.parse(lines[0]!);
      e.outputDecision = { tampered: true };
      lines[0] = JSON.stringify(e);
      fs.writeFileSync(path, lines.join('\n') + '\n');

      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const code = await verifyCommand(config, { report: 'report.json' }, cap.io);
      expect(code).toBe(1);
      const report = JSON.parse(readFileSync(join(cwd, 'report.json'), 'utf8'));
      expect(report.chain.valid).toBe(false);
      expect(report.chain.brokenAt).toBe(0);
      expect(report.chain.reason).toBe('entry_hash_mismatch');
      expect(typeof report.chain.detail).toBe('string');
    });
  });

  describe('anchor', () => {
    it('emits an anchor JSON for the tail of the chain', async () => {
      await seedEntries(dir, 5);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const code = await anchorCommand(config, {}, cap.io);
      expect(code).toBe(0);
      const anchor = JSON.parse(cap.out().trim());
      expect(anchor.systemId).toBe('sys-cli');
      expect(anchor.sequence).toBe(4);
      expect(anchor.entryCount).toBe(5);
      expect(anchor.recordHash).toMatch(/^sha256:[0-9a-f]{64}$/);
      expect(anchor.algorithm).toBe('sha256');
      expect(typeof anchor.signature).toBe('string');
      expect(anchor.signature.length).toBeGreaterThan(0);
      expect(typeof anchor.anchoredAt).toBe('string');
      expect(typeof anchor.cliVersion).toBe('string');
    });

    it('writes anchor JSON to a file when --output is given', async () => {
      await seedEntries(dir, 2);
      const config = resolveConfig(null, { systemId: 'sys-cli', storageDir: dir });
      const cap = captureIO(cwd);
      const outFile = join(cwd, 'chain-head.json');
      const code = await anchorCommand(config, { output: outFile }, cap.io);
      expect(code).toBe(0);
      const anchor = JSON.parse(readFileSync(outFile, 'utf8'));
      expect(anchor.entryCount).toBe(2);
      expect(cap.err()).toMatch(/Wrote anchor/);
    });

    it('returns 2 when no entries match the system id', async () => {
      const config = resolveConfig(null, { systemId: 'sys-empty', storageDir: dir });
      const cap = captureIO(cwd);
      const code = await anchorCommand(config, {}, cap.io);
      expect(code).toBe(2);
      expect(cap.err()).toMatch(/no entries found/);
    });
  });
});
