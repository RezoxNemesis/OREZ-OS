import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Store', exact: true }).click();
});
test.afterEach(async ({ page }, info) => {
  await page.screenshot({ path: info.outputPath('full-page.png'), fullPage: true });
});

test('store lists requested apps and clearly separates preview from installation', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'OREZ Store' })).toBeVisible();
  await expect(page.getByText('This browser preview cannot install or launch apps.', { exact: false })).toBeVisible();
  for (const name of ['YouTube','Instagram','Brave Browser','Google Chrome','Free Fire','Subway Surfers','Asphalt Legends','Google Play Store']) {
    await expect(page.locator('.store-app').filter({ hasText: name }).first()).toBeVisible();
  }
  await expect(page.getByRole('button', { name: 'Android runtime pending' })).toBeDisabled();
  await expect(page.getByText('Optional paid features remain publisher-controlled.')).toBeVisible();
  await expect(page.locator('.store-app').first()).toContainText('Android');
  await expect(page.getByLabel('App format').locator('option[value=web]')).toHaveCount(0);
  for (const name of ['Brave Browser (Linux)','Google Chrome (Linux)']) {
    await expect(page.locator('.store-app').filter({ hasText: name })).toContainText('Native Linux');
  }
  await expect(page.locator('.store-app')).toHaveCount(10);
});
test('search, format filter and empty results work', async ({ page }) => {
  await page.getByLabel('Search apps', { exact: true }).fill('subway');
  await expect(page.locator('.store-app')).toHaveCount(1);
  await expect(page.getByRole('heading', { name: 'Subway Surfers' })).toBeVisible();
  await page.getByLabel('App format', { exact: true }).selectOption('native');
  await expect(page.getByText('No matching apps. Try another search.')).toBeVisible();
  await page.getByLabel('Search apps', { exact: true }).fill('');
  await expect(page.locator('.store-app')).toHaveCount(4);
});
test('Android games stay blocked with permissions and official source visible', async ({ page }) => {
  await page.locator('.store-app').filter({ hasText: 'Free Fire' }).click();
  await expect(page.getByRole('button', { name: 'Android runtime pending' })).toBeDisabled();
  await expect(page.getByText('Never bypass anti-cheat', { exact: false })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Official website for Free Fire' })).toHaveAttribute('href','https://play.google.com/store/apps/details?id=com.dts.freefireth');
});
test('store is accessible and stays within viewport', async ({ page }) => {
  const audit = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
  expect(audit.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
