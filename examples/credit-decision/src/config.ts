/**
 * Underwriting policy parameters for the credit-decision example.
 *
 * Lifted out of ``index.ts`` so they can be tuned (or replaced from a JSON
 * policy file) without touching the audit logging flow. None of these
 * numbers are magic literals — each comes from a documented credit policy
 * and the version is recorded as ``modelConfiguration.policyVersion`` in
 * every audit entry.
 */

export interface CreditPolicyConfig {
  /** Policy version recorded in modelConfiguration. Bump on any field change. */
  policyVersion: string;
  /** Prompt template version stamped into the audit entry. */
  promptTemplateVersion: string;
  /** Minimum credit score (FICO-like 300-850 scale) to consider for any approval. */
  minCreditScore: number;
  /** Credit score at and above which the borrower qualifies for the prime APR tier. */
  primeCreditScore: number;
  /** Maximum debt-to-income ratio before escalation to human review. */
  maxDti: number;
  /** Default term length in months for approved loans. */
  termMonths: number;
  /** APR (basis points) for prime-tier borrowers. */
  aprBpsPrime: number;
  /** APR (basis points) for standard-tier borrowers. */
  aprBpsStandard: number;
  /** Multiplier on requested amount used to estimate additional monthly debt service. */
  requestedAmountServicingFactor: number;
  /** Manual-underwriting override loan limit applied after escalation. */
  manualOverrideLimit: number;
  /** Manual-underwriting override APR (basis points) applied after escalation. */
  manualOverrideAprBps: number;
  /** Reviewer ID stamped onto the human-review record for the example. */
  reviewerId: string;
}

export const CREDIT_POLICY: CreditPolicyConfig = {
  policyVersion: '7.1',
  promptTemplateVersion: '7.1.0',
  minCreditScore: 640,
  primeCreditScore: 750,
  maxDti: 0.45,
  termMonths: 36,
  aprBpsPrime: 750,
  aprBpsStandard: 1250,
  requestedAmountServicingFactor: 0.05,
  manualOverrideLimit: 8000,
  manualOverrideAprBps: 1500,
  reviewerId: 'credit-officer-12',
} as const;
