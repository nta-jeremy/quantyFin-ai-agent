import { test, expect } from '@playwright/test';

test('login flow E2E test', async ({ page }) => {
  // Navigate to root route
  await page.goto('/');

  // Expect login title to be present
  await expect(page.locator('h1')).toHaveText('QuantyFin AI');

  // Fill in login credentials
  await page.fill('input[name="email"]', 'admin@quantyfin.ai');
  await page.fill('input[name="password"]', 'password123');

  // Click login button
  await page.click('button[type="submit"]');

  // Expect successful login message to be visible
  await expect(page.locator('#welcome-message')).toHaveText('Chào mừng bạn đến với QuantyFin!');
});
