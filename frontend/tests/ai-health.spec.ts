import { test, expect } from '@playwright/test';

test('AI Pipeline Health screen E2E test', async ({ page }) => {
  // Navigate to root route
  await page.goto('/');

  // Expect login form to be visible
  await expect(page.locator('.qf-login')).toBeVisible();

  // Fill in login credentials
  await page.fill('input[name="email"]', 'admin@quantyfin.ai');
  await page.fill('input[name="password"]', 'password123');

  // Click login button
  await page.click('button[type="submit"]');

  // Expect successful login by verifying dashboard shell is visible
  await expect(page.locator('.app-shell')).toBeVisible();

  // Click on the AI Pipeline Health side link
  await page.click('button:has-text("AI Pipeline Health")');

  // Verify the screen is displayed by checking for its ID and title
  await expect(page.locator('#screen-ai-health')).toBeVisible();
  await expect(page.locator('h1')).toHaveText('Trạng thái & Hiệu suất AI Pipeline');

  // Verify KPI cards are rendered
  await expect(page.locator('.kpi-card:has-text("Tổng Token (24h)")')).toBeVisible();
  await expect(page.locator('.kpi-card:has-text("Chi phí ước tính")')).toBeVisible();
  await expect(page.locator('.kpi-card:has-text("Độ trễ trung bình")')).toBeVisible();
  await expect(page.locator('.kpi-card:has-text("Hiệu suất trích xuất")')).toBeVisible();

  // Verify pipeline flow
  await expect(page.locator('.pipe')).toBeVisible();
  await expect(page.locator('.stage:has-text("LLM Extractor")')).toBeVisible();
  await expect(page.locator('.stage.active')).toBeVisible();

  // Verify details table
  await expect(page.locator('table.dt')).toBeVisible();
  await expect(page.locator('tr:has-text("Haiku 3.5")')).toBeVisible();

  // Verify settings panel
  await expect(page.locator('.qf-card:has-text("AI Engine Settings")')).toBeVisible();
});
