import { z } from 'zod';

export const SCHEMA_VERSION = 'vouchrail-v1.0' as const;

// ISO-8601 UTC with explicit second range 00-59 (no leap-seconds; Date.parse rejects 60).
const ISO_DATETIME_REGEX =
  /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d{1,9})?(Z|[+-](0\d|1\d|2[0-3]):[0-5]\d)$/;

const SHA256_HEX_REGEX = /^[0-9a-f]{64}$/;

const isoDateTime = z.string().regex(ISO_DATETIME_REGEX, 'must be ISO-8601 UTC');
const sha256Hex = z.string().regex(SHA256_HEX_REGEX, 'must be 64-char lowercase hex');

export const ModelProviderEnum = z.union([
  z.literal('anthropic'),
  z.literal('openai'),
  z.literal('google'),
  z.literal('azure'),
  z.literal('self_hosted'),
  z.string().min(1),
]);
export type ModelProvider = z.infer<typeof ModelProviderEnum>;

export const HumanReviewDecisionEnum = z.union([
  z.literal('approve'),
  z.literal('override'),
  z.literal('escalate'),
]);
export type HumanReviewDecision = z.infer<typeof HumanReviewDecisionEnum>;

export const ToolCallSchema = z
  .object({
    toolName: z.string().min(1),
    toolVersion: z.string().optional(),
    inputFingerprint: sha256Hex,
    outputFingerprint: sha256Hex,
    startedAt: isoDateTime,
    endedAt: isoDateTime,
    error: z.string().optional(),
  })
  .strict();
export type ToolCall = z.infer<typeof ToolCallSchema>;

export const HumanReviewSchema = z
  .object({
    reviewerId: z.string().min(1),
    reviewedAt: isoDateTime,
    decision: HumanReviewDecisionEnum,
    rationale: z.string().optional(),
    finalDecision: z.unknown().optional(),
  })
  .strict();
export type HumanReview = z.infer<typeof HumanReviewSchema>;

const PiiRedactedSchema = z
  .object({
    fields: z.array(z.string().min(1)),
    pseudonymKey: z.string().optional(),
  })
  .strict();

const ModelConfigurationSchema = z
  .object({
    temperature: z.number().optional(),
    maxTokens: z.number().int().nonnegative().optional(),
    topP: z.number().optional(),
  })
  .catchall(z.unknown());

const AuditLogEntryBase = z
  .object({
    schemaVersion: z.literal(SCHEMA_VERSION),
    recordedBy: z.string().min(1),

    callId: z.string().min(1),
    parentCallId: z.string().optional(),
    caseId: z.string().min(1),
    sessionId: z.string().optional(),
    systemId: z.string().min(1),

    startedAt: isoDateTime,
    endedAt: isoDateTime,
    durationMs: z.number().int().nonnegative(),

    modelProvider: ModelProviderEnum,
    modelName: z.string().min(1),
    modelVersion: z.string().min(1),
    modelConfiguration: ModelConfigurationSchema,

    promptTemplateId: z.string().min(1),
    promptTemplateVersion: z.string().min(1),
    promptFingerprint: sha256Hex,

    inputFingerprint: sha256Hex,
    inputPiiRedacted: PiiRedactedSchema.optional(),
    referenceDatabase: z.string().optional(),

    toolCalls: z.array(ToolCallSchema).optional(),

    outputFingerprint: sha256Hex,
    outputDecision: z.unknown(),
    reasonCodes: z.array(z.string().min(1)).optional(),

    operatorId: z.string().min(1),
    humanReview: HumanReviewSchema.optional(),

    riskFlags: z.array(z.string().min(1)).optional(),
    incidentId: z.string().optional(),

    entryHash: sha256Hex,
    // Always set: GENESIS_PREVIOUS_HASH for the first entry, prior entryHash thereafter.
    previousEntryHash: sha256Hex,
    signature: z.string().min(1),
  })
  .strict();

export const AuditLogEntrySchema = AuditLogEntryBase;
export type AuditLogEntry = z.infer<typeof AuditLogEntrySchema>;

/**
 * Schema for an entry *before* hash chain linking and signing.
 * The SDK fills the user-facing fields; entryHash / previousEntryHash /
 * signature are added by the chain layer.
 */
export const AuditLogEntryInputSchema = AuditLogEntryBase.omit({
  entryHash: true,
  previousEntryHash: true,
  signature: true,
});
export type AuditLogEntryInput = z.infer<typeof AuditLogEntryInputSchema>;
