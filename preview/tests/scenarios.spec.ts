import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

test.afterEach(async ({ page }, info) => {
  await page.screenshot({ path: info.outputPath('full-page.png'), fullPage: true });
  await info.attach('full-page', { path: info.outputPath('full-page.png'), contentType: 'image/png' });
});

for (const value of ['invalid JSON', 'null', '[]', '42', '{"glass":"false","contrast":1,"motion":null}']) {
  test(`malformed saved preferences recover: ${value}`, async ({ page }) => {
    await page.addInitScript(value => localStorage.setItem('orez.preview.preferences.v1', value), value);
    await page.goto('/');
    await page.getByRole('button', { name: 'Settings', exact: true }).click();
    await expect(page.getByRole('switch', { name: 'Frosted panels' })).toBeChecked();
    await expect(page.getByRole('switch', { name: 'High contrast' })).not.toBeChecked();
  });
}

test('blocked browser storage stays usable without uncaught errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    for (const name of ['localStorage', 'sessionStorage']) Object.defineProperty(window, name, { get() { throw new DOMException('Storage blocked', 'SecurityError'); } });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('switch', { name: 'High contrast' }).click();
  await expect(page.getByRole('switch', { name: 'High contrast' })).toBeChecked();
  await expect(page.getByRole('status')).toContainText('Storage unavailable');
  await page.evaluate(async () => { await navigator.serviceWorker.ready; });
  await expect.poll(() => page.evaluate(() => !!navigator.serviceWorker.controller)).toBe(true);
  expect(errors).toEqual([]);
});

test('storage quota failure reports session-only preferences', async ({ page }) => {
  await page.addInitScript(() => { Storage.prototype.setItem = () => { throw new DOMException('Full', 'QuotaExceededError'); }; });
  await page.goto('/');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('switch', { name: 'High contrast' }).click();
  await expect(page.getByRole('status')).toContainText('Changes last until this page closes');
  await page.reload();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'High contrast' })).not.toBeChecked();
});

test('injected worker-registration failure leaves ordinary navigation working', async ({ page }) => {
  await page.addInitScript(() => { navigator.serviceWorker.register = () => Promise.reject(new DOMException('Registration unavailable', 'SecurityError')); });
  await page.goto('/');
  await expect(page.getByRole('status')).toContainText('Offline preview unavailable');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
});

test('real service worker update reloads after consent with browser storage blocked', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    for (const name of ['localStorage', 'sessionStorage']) Object.defineProperty(window, name, { get() { throw new DOMException('Storage blocked', 'SecurityError'); } });
  });
  await page.goto('/');
  await expect.poll(() => page.evaluate(() => !!navigator.serviceWorker.controller)).toBe(true);
  const workerFile = fileURLToPath(new URL('../../dist/preview/sw.js', import.meta.url));
  const original = await readFile(workerFile, 'utf8');
  try {
    // Change only a generated build artifact; source files are never changed.
    await writeFile(workerFile, original + `\n// Test update ${Date.now()}\n`);
    await page.evaluate(async () => { const registration = await navigator.serviceWorker.getRegistration(); await registration!.update(); });
    await expect(page.getByRole('button', { name: 'Apply update' })).toBeVisible();
    await page.screenshot({ path: test.info().outputPath('update-awaiting-consent.png'), fullPage: true });
    await Promise.all([page.waitForEvent('load'), page.getByRole('button', { name: 'Apply update' }).click()]);
    await expect(page.getByRole('heading', { name: 'Make room for what matters.' })).toBeVisible();
    expect(errors).toEqual([]);
  } finally {
    await writeFile(workerFile, original);
  }
});

test('empty search recovers after hostile-looking literal input', async ({ page }) => {
  const dialogs: string[] = [];
  page.on('dialog', async dialog => { dialogs.push(dialog.message()); await dialog.dismiss(); });
  await page.goto('/');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByLabel('Search preview settings').fill('<img src=x onerror=alert("injected")>');
  await expect(page.getByRole('switch')).toHaveCount(0);
  await page.getByLabel('Search preview settings').fill('  CONTRAST ');
  await expect(page.getByRole('switch')).toHaveCount(1);
  await page.getByLabel('Search preview settings').clear();
  await expect(page.getByRole('switch')).toHaveCount(3);
  expect(dialogs).toEqual([]);
});

test('repeated toggles and navigation preserve effective preference state', async ({ page }) => {
  await page.goto('/');
  for (let index = 0; index < 12; index++) {
    await page.getByRole('button', { name: 'Settings', exact: true }).click();
    await page.getByRole('switch', { name: 'High contrast' }).click();
    await page.getByRole('button', { name: 'Workspace', exact: true }).click();
  }
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'High contrast' })).not.toBeChecked();
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('orez.preview.preferences.v1')!).contrast)).toBe(false);
});

test('demo pairing and consent disappear on browser reload', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByRole('button', { name: 'Try demo pairing' }).click();
  await page.getByRole('switch', { name: 'Clipboard permission' }).click();
  await page.reload();
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Try demo pairing' })).toBeVisible();
  await expect(page.getByRole('switch', { name: 'Clipboard permission' })).toHaveCount(0);
});

test('demo controls never call privileged browser APIs', async ({ page }) => {
  await page.addInitScript(() => {
    (window as any).sensitiveCalls = [];
    for (const [name, methods] of Object.entries({ clipboard: ['read', 'readText', 'write', 'writeText'], mediaDevices: ['getUserMedia'], geolocation: ['getCurrentPosition', 'watchPosition'] })) {
      Object.defineProperty(navigator, name, { value: Object.fromEntries(methods.map(method => [method, () => { (window as any).sensitiveCalls.push(`${name}.${method}`); return Promise.reject(new Error('Forbidden in preview')); }])) });
    }
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByRole('button', { name: 'Try demo pairing' }).click();
  await page.getByRole('switch', { name: 'Clipboard permission' }).click();
  await page.getByRole('button', { name: 'Revoke demo device' }).click();
  await page.getByRole('button', { name: 'Installation', exact: true }).click();
  expect(await page.evaluate(() => (window as any).sensitiveCalls)).toEqual([]);
});

test('offline reload retains local settings', async ({ page, context }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('switch', { name: 'High contrast' }).click();
  await expect.poll(() => page.evaluate(() => !!navigator.serviceWorker.controller)).toBe(true);
  await context.setOffline(true);
  await page.reload();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'High contrast' })).toBeChecked();
  await page.getByRole('switch', { name: 'Frosted panels' }).click();
  await expect(page.getByRole('switch', { name: 'Frosted panels' })).not.toBeChecked();
});

test('solid panels disable blur and persist after restart', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('switch', { name: 'Frosted panels' }).click();
  await expect(page.locator('.panel')).toHaveCSS('backdrop-filter', 'none');
  await page.reload();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.locator('.panel')).toHaveCSS('backdrop-filter', 'none');
});

for (const screen of ['Workspace', 'Settings', 'Connect', 'Installation']) {
  test(`automated WCAG A/AA checks: ${screen}`, async ({ page }, info) => {
    await page.goto('/');
    await page.getByRole('button', { name: screen, exact: true }).click();
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    await info.attach('axe-results', { body: JSON.stringify(result, null, 2), contentType: 'application/json' });
    expect(result.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.map(n => n.target) }))).toEqual([]);
  });
}

for (const viewport of [{width:320,height:568}, {width:915,height:412}, {width:1920,height:1080}, {width:2560,height:1440}]) {
  test(`responsive layout ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto('/');
    for (const screen of ['Workspace', 'Settings', 'Connect', 'Installation']) {
      await page.getByRole('button', { name: screen, exact: true }).click();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await expect(page.getByRole('button', { name: screen, exact: true })).toBeInViewport();
      await page.screenshot({ path: test.info().outputPath(`${screen.toLowerCase()}.png`), fullPage: true });
    }
  });
}
