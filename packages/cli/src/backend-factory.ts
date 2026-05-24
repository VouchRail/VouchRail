import {
  VouchRailConfigError,
  ERROR_CODES,
  LocalStorageBackend,
  S3StorageBackend,
  type StorageBackend,
} from '@vouchrail/sdk';

import type { CliConfigStorage } from './config.js';

export function createBackend(storage: CliConfigStorage): StorageBackend {
  switch (storage.type) {
    case 'local':
      return new LocalStorageBackend(storage);
    case 's3':
      return new S3StorageBackend(storage);
    default: {
      const _exhaustive: never = storage;
      throw new VouchRailConfigError(
        ERROR_CODES.CONFIG_UNKNOWN_BACKEND,
        `createBackend: unknown storage type (${JSON.stringify(_exhaustive)})`,
        { received: storage },
      );
    }
  }
}
