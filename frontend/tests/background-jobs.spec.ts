import { test, expect } from '@playwright/test';

test('AI Background Jobs E2E test', async ({ page }) => {
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

  // Click on the Pipeline & Jobs side link
  await page.click('button:has-text("Pipeline & Jobs")');

  // Verify the screen is displayed by checking for its header
  await expect(page.locator('h1')).toHaveText('Crawler jobs & ingestion pipeline');

  // Verify Segment tab switcher is visible and defaults to "Trình thu thập dữ liệu (Crawler Jobs)"
  const tabCrawler = page.locator('button:has-text("Trình thu thập dữ liệu (Crawler Jobs)")');
  const tabAi = page.locator('button:has-text("Tác vụ AI Chạy nền (AI Agent Jobs)")');
  await expect(tabCrawler).toBeVisible();
  await expect(tabAi).toBeVisible();

  // Click "Tác vụ AI Chạy nền" tab
  await tabAi.click();

  // Verify the title of the table changes to "Tác vụ AI Chạy nền"
  await expect(page.locator('h3:has-text("Tác vụ AI Chạy nền")')).toBeVisible();

  // Verify AI jobs table columns are displayed
  await expect(page.locator('th:has-text("Tên tác vụ (Task)")')).toBeVisible();
  await expect(page.locator('th:has-text("Phân loại (Type)")')).toBeVisible();
  await expect(page.locator('th:has-text("Trạng thái (Status)")')).toBeVisible();

  // Verify mock data entries are present in the table
  const completedJobRow = page.locator('tr:has-text("Phân tích rủi ro danh mục tự động")');
  const runningJobRow = page.locator('tr:has-text("Tổng hợp báo cáo tài chính FPT")');
  const failedJobRow = page.locator('tr:has-text("Giám sát watchlist cổ phiếu")');

  await expect(completedJobRow).toBeVisible();
  await expect(runningJobRow).toBeVisible();
  await expect(failedJobRow).toBeVisible();

  // Verify progress bar is visible on the row
  await expect(completedJobRow.locator('div[style*="width"]').first()).toBeVisible();

  // Click on Completed job row to open JobDetailsModal
  await completedJobRow.click();

  // Verify Completed job details modal is opened
  const modalHeader = page.locator('h3:has-text("Chi tiết Tác vụ AI")');
  const modalContainer = page.locator('div:has(> div > h3:has-text("Chi tiết Tác vụ AI"))');
  await expect(modalHeader).toBeVisible();
  await expect(modalContainer.locator('text=Completed')).toBeVisible();
  await expect(modalContainer.locator('h5:has-text("Kết quả phân tích")')).toBeVisible();

  // Close modal by clicking "Đóng" button
  await page.click('button:has-text("Đóng")');
  await expect(modalHeader).not.toBeVisible();

  // Click on Failed job row to open JobDetailsModal
  await failedJobRow.click();
  await expect(modalHeader).toBeVisible();
  await expect(modalContainer.locator('text=Failed')).toBeVisible();
  await expect(modalContainer.locator('text=Log lỗi (Error Log)')).toBeVisible();

  // Verify the error log pre block is red
  const errorLogPre = modalContainer.locator('pre');
  await expect(errorLogPre).toBeVisible();
  await expect(errorLogPre).toHaveCSS('color', 'rgb(239, 68, 68)');

  // Close modal by clicking the X close button
  await modalContainer.locator('button').first().click();
  await expect(modalHeader).not.toBeVisible();
});
