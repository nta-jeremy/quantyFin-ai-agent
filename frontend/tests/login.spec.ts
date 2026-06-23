import { test, expect } from '@playwright/test';

test('login, navigation, scenario switching and logout flow E2E test', async ({ page }) => {
  // Navigate to root route
  await page.goto('/');

  // Expect login form to be visible
  await expect(page.locator('.qf-login')).toBeVisible();

  // Test invalid login
  await page.fill('input[name="email"]', 'wrong@quantyfin.ai');
  await page.fill('input[name="password"]', 'wrongpassword');
  await page.click('button[type="submit"]');

  // Expect error message to be visible
  await expect(page.locator('text=Email hoặc mật khẩu không chính xác.')).toBeVisible();

  // Fill in correct login credentials
  await page.fill('input[name="email"]', 'admin@quantyfin.ai');
  await page.fill('input[name="password"]', 'password123');

  // Click login button
  await page.click('button[type="submit"]');

  // Expect successful login by verifying dashboard shell is visible
  await expect(page.locator('.app-shell')).toBeVisible();

  // Verify default scenario banner is "Biến động mạnh" (since volatile is the default in App.tsx)
  await expect(page.locator('.scenario-banner')).toHaveText('Biến động mạnh');

  // Test Scenario Switcher - Up
  await page.selectOption('select', 'up');
  await expect(page.locator('.scenario-banner')).toHaveText('Thị trường tăng');

  // Test Scenario Switcher - Down
  await page.selectOption('select', 'down');
  await expect(page.locator('.scenario-banner')).toHaveText('Thị trường giảm');

  // Test Scenario Switcher - Crisis
  await page.selectOption('select', 'crisis');
  await expect(page.locator('.scenario-banner')).toHaveText('Khủng hoảng');

  // Test click search input redirects to AI Chat
  await page.click('.top-bar__search input');
  await expect(page.locator('.nav-link[data-active="true"]')).toContainText('AI Chat');

  // Test logout
  await page.click('button[title="Đăng xuất"]');

  // Expect redirect back to Login screen
  await expect(page.locator('.qf-login')).toBeVisible();

  // Verify localStorage qf_auth is '0'
  const qfAuth = await page.evaluate(() => localStorage.getItem('qf_auth'));
  expect(qfAuth).toBe('0');
});
