import { test, expect } from '@playwright/test';

test.afterEach(async ({ page }, info) => {
  await page.screenshot({ path: info.outputPath('full-page.png'), fullPage: true });
  await info.attach('full-page', { path: info.outputPath('full-page.png'), contentType: 'image/png' });
});

test('workspace loads without remote requests or horizontal overflow', async ({ page }) => {
  const external: string[] = [];
  const errors: string[] = [];
  page.on('request', request => { if (!request.url().startsWith('http://127.0.0.1:4173/') && !request.url().startsWith('data:')) external.push(request.url()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Make room for what matters.' })).toBeVisible();
  await expect(page.getByText('No access to your disks', { exact: false })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
});

test('appearance preferences persist and reset without OS permissions', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('switch', { name: 'High contrast' }).click();
  await page.getByRole('switch', { name: 'Frosted panels' }).click();
  await page.reload();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'High contrast' })).toBeChecked();
  await expect(page.getByRole('switch', { name: 'Frosted panels' })).not.toBeChecked();
  await page.screenshot({ path: test.info().outputPath('high-contrast.png'), fullPage: true });
  await page.getByRole('button', { name: 'Reset preview preferences' }).click();
  await expect(page.getByRole('switch', { name: 'High contrast' })).not.toBeChecked();
  await expect(page.getByRole('switch', { name: 'Frosted panels' })).toBeChecked();
});

test('demo device consent is revoked with pairing', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByRole('button', { name: 'Try demo pairing' }).click();
  await page.getByRole('switch', { name: 'Clipboard permission' }).click();
  await expect(page.getByRole('switch', { name: 'Clipboard permission' })).toBeChecked();
  await page.getByRole('button', { name: 'Revoke demo device' }).click();
  await expect(page.getByRole('status')).toHaveText('Demo pairing and permissions revoked.');
  await page.getByRole('button', { name: 'Try demo pairing' }).click();
  await expect(page.getByRole('switch', { name: 'Clipboard permission' })).not.toBeChecked();
});

test('installation is visibly blocked and has no disk action', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Installation', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Installation unavailable' })).toBeDisabled();
  await expect(page.getByText('No drive has been detected', { exact: false })).toBeVisible();
  await expect(page.getByText('Keep your Windows recovery USB.', { exact: false })).toBeVisible();
});

test('keyboard access and reduced motion work', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to workspace' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'Gentle motion' })).not.toBeChecked();
  await page.getByLabel('Search preview settings').fill('contrast');
  await expect(page.getByRole('switch')).toHaveCount(1);
});

test('installed service worker serves preview offline', async ({ page, context }) => {
  await page.goto('/');
  await expect.poll(() => page.evaluate(async () => (await navigator.serviceWorker.getRegistration())?.active?.state || 'not active'), { timeout: 10000 }).toBe('activated');
  await expect.poll(() => page.evaluate(() => !!navigator.serviceWorker.controller)).toBe(true);
  await context.setOffline(true);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Make room for what matters.' })).toBeVisible();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
});

test('portable export has no companion asset requests', async ({ page }) => {
  const requests: string[] = [];
  page.on('request', request => { if (!request.url().startsWith('data:')) requests.push(request.url()); });
  await page.goto('/portable.html');
  await expect(page.getByRole('heading', { name: 'Make room for what matters.' })).toBeVisible();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'High contrast' })).toBeVisible();
  expect(requests).toEqual(['http://127.0.0.1:4173/portable.html']);
});
