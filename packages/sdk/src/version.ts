import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

interface PackageManifest {
  name: string;
  version: string;
}

function locateManifest(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  return join(here, '..', 'package.json');
}

const manifest = JSON.parse(readFileSync(locateManifest(), 'utf8')) as PackageManifest;

export const SDK_NAME = manifest.name;
export const SDK_VERSION = manifest.version;
export const RECORDED_BY = `${SDK_NAME}@${SDK_VERSION}`;
