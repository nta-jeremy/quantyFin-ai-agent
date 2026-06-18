import { test, expect } from '@playwright/test';

test('login flow E2E test', async ({ page }) => {
  // Navigate to root route
  await page.goto('/');

  // Expect login form to be visible (instead of incorrect static h1)
  await expect(page.locator('.qf-login')).toBeVisible();

  // Fill in login credentials
  await page.fill('input[name="email"]', 'admin@quantyfin.ai');
  await page.fill('input[name="password"]', 'password123');

  // Click login button (which now has type="submit")
  await page.click('button[type="submit"]');

  // Expect successful login by verifying dashboard shell is visible (language-independent)
  await expect(page.locator('.app-shell')).toBeVisible();
});
