import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';
export default defineConfig({
  testDir: './tests',
  outputDir: process.env.OREZ_EVIDENCE_DIR ? `${process.env.OREZ_EVIDENCE_DIR}/ui` : '../dist/evidence/preview-browser',
  fullyParallel: false, workers: 1, retries: 0, timeout: 30000,
  reporter: [['list'], ['html', { outputFolder: process.env.OREZ_EVIDENCE_DIR ? `${process.env.OREZ_EVIDENCE_DIR}/playwright-report` : '../dist/evidence/preview-playwright-report', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    screenshot: 'on', trace: 'retain-on-failure',
    launchOptions: { executablePath: process.env.OREZ_CHROMIUM || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined) }
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 960 } } },
    { name: 'mobile', use: { viewport: { width: 412, height: 915 }, isMobile: true, hasTouch: true } }
  ],
  webServer: {
    command: 'npx vite preview --config preview/vite.config.ts --host 127.0.0.1 --port 4173 --strictPort',
    cwd: '..', port: 4173, reuseExistingServer: false
  }
});
