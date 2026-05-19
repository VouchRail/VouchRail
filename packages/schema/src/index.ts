export {
  SCHEMA_VERSION,
  type ModelProvider,
  type HumanReviewDecision,
  type ToolCall,
  type HumanReview,
  type AuditLogEntry,
  type AuditLogEntryInput,
  ToolCallSchema,
  HumanReviewSchema,
  AuditLogEntrySchema,
  AuditLogEntryInputSchema,
} from './types.js';

export { canonicalize, canonicalizeForHash } from './canonicalize.js';

export {
  HASH_ALGORITHM,
  GENESIS_PREVIOUS_HASH,
  computeEntryHash,
  linkEntry,
  verifyEntryHash,
  verifyChain,
  type ChainVerificationResult,
} from './hash-chain.js';
