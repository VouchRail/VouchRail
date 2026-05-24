import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    env: {
      // Tests construct InlineSigner repeatedly; the one-time dev-only
      // warning is verified by signing.test.ts and silenced everywhere else.
      VOUCHRAIL_SUPPRESS_INLINE_WARNING: '1',
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.ts'],
      exclude: [
        '**/*.test.ts',
        'dist/**',
        'node_modules/**',
        'src/index.ts',
        'src/config.ts',
        'src/backends/types.ts',
      ],
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 70,
        statements: 85,
      },
    },
  },
});
