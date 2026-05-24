/**
 * Helpers reused by every provider adapter. Adapters interact with arbitrary
 * provider SDK request/response shapes through structural typing, so we keep
 * the helpers untyped (`unknown`) at the boundary and let each adapter cast
 * its inputs.
 */

export function pickKeys(
  params: Record<string, unknown>,
  keys: readonly string[],
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const key of keys) {
    if (key in params) out[key] = params[key];
  }
  return out;
}

export function extractOutput(response: unknown, keys: readonly string[]): unknown {
  if (response && typeof response === 'object') {
    const r = response as Record<string, unknown>;
    const out: Record<string, unknown> = {};
    for (const key of keys) out[key] = r[key];
    return out;
  }
  return response ?? null;
}
