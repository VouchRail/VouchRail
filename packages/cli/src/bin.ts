#!/usr/bin/env node
import { runCli } from './program.js';

runCli().then(
  (code) => {
    if (code) process.exit(code);
  },
  (err) => {
    process.stderr.write(`auditlayer: ${(err as Error).message}\n`);
    process.exit(1);
  },
);
