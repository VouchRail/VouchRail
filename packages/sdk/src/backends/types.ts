import type { AuditLogEntry } from '@vouchrail/schema';

export interface AppendOptions {
  systemId: string;
}

export interface QueryOptions {
  systemId: string;
  from?: string;
  to?: string;
  caseId?: string;
}

export interface StorageBackend {
  /** Append a single audit log entry. Implementations should be atomic per-entry. */
  append(entry: AuditLogEntry, opts: AppendOptions): Promise<void>;

  /** Iterate entries in chronological order (best effort). */
  list(opts: QueryOptions): AsyncIterable<AuditLogEntry>;

  /** Optional: cleanup any open resources. */
  close?(): Promise<void> | void;
}
