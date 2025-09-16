/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
    css: true,
    reporters: ['verbose'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/coverage/**',
        'dist/',
        'build/',
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        'src/vite-env.d.ts',
        'src/main.tsx',
      ],
      thresholds: {
        global: {
          branches: 70,
          functions: 70,
          lines: 70,
          statements: 70,
        },
      },
    },
    include: [
      'src/**/*.{test,spec}.{js,ts,jsx,tsx}',
    ],
    exclude: [
      'node_modules/',
      'dist/',
      'build/',
      '.git/',
    ],
    watchExclude: [
      'node_modules/**',
      'dist/**',
      'build/**',
    ],
    testTimeout: 10000,
    hookTimeout: 10000,
    pool: 'threads',
    poolOptions: {
      threads: {
        minThreads: 1,
        maxThreads: 4,
      },
    },
    logLevel: 'info',
    silent: false,
    ui: true,
    open: false,
  },
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
      '@components': new URL('./src/components', import.meta.url).pathname,
      '@pages': new URL('./src/pages', import.meta.url).pathname,
      '@services': new URL('./src/services', import.meta.url).pathname,
      '@stores': new URL('./src/stores', import.meta.url).pathname,
      '@types': new URL('./src/types', import.meta.url).pathname,
      '@utils': new URL('./src/utils', import.meta.url).pathname,
      '@styles': new URL('./src/styles', import.meta.url).pathname,
      '@assets': new URL('./src/assets', import.meta.url).pathname,
    },
  },
});