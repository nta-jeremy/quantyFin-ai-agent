import { test, expect, type Page } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';

async function loginAndGoToDashboard(page: Page) {
  await page.goto(BASE_URL);
  await page.evaluate(() => localStorage.setItem('qf_auth', '1'));
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
}

test.describe('Dashboard & Stock Detail Screen E2E Flows', () => {
  test('TC1: Dashboard load, hiển thị Market Summary, Portfolio, Top Movers và chuyển hướng sang Stock Detail', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Verify Market Summary cards (VN-Index, HNX, UPCoM)
    const vniCard = page.locator('.kpi-card .label', { hasText: 'VN-Index' }).first();
    await expect(vniCard).toBeVisible();

    const hnxCard = page.locator('.kpi-card .label', { hasText: 'HNX-Index' }).or(page.locator('.kpi-card .label', { hasText: 'HNX' })).first();
    await expect(hnxCard).toBeVisible();

    // Verify AI Briefing section is visible
    await expect(page.locator('text=AI Briefing')).toBeVisible();

    // Verify Portfolio Snapshot section and assets table
    await expect(page.locator('text=Danh mục đầu tư')).toBeVisible();
    await expect(page.locator('text=Tổng giá trị tài sản')).toBeVisible();

    // Verify Top Movers widget is visible
    await expect(page.locator('text=Top Movers hôm nay')).toBeVisible();
    await expect(page.locator('text=Tăng mạnh nhất')).toBeVisible();
    await expect(page.locator('text=Giảm mạnh nhất')).toBeVisible();

    // Click on a stock ticker in the Watchlist table (e.g., FPT or VHM)
    const stockRow = page.locator('table.dt button').filter({ hasText: 'FPT' }).first();
    await expect(stockRow).toBeVisible();
    await stockRow.click();

    // Verify routing to Stock Detail screen
    await expect(page.locator('.qf-pagehead h1')).toContainText('FPT');
    
    // Verify basic info: volume
    await expect(page.locator('text=KL: ')).toBeVisible();

    // Verify financial metrics cards
    await expect(page.locator('.kpi-card .label', { hasText: 'Vốn hóa' }).first()).toBeVisible();
    await expect(page.locator('.kpi-card .label', { hasText: 'P/E · P/B' }).first()).toBeVisible();
    await expect(page.locator('.kpi-card .label', { hasText: 'EPS · Cổ tức' }).first()).toBeVisible();

    // Verify AI Thesis section
    await expect(page.locator('text=AI Thesis')).toBeVisible();
  });

  test('TC2: AI Confidence Indicator ẩn/hiển thị dựa trên tweaks panel', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Go to Stock Detail screen (click FPT)
    const stockRow = page.locator('table.dt button').filter({ hasText: 'FPT' }).first();
    await expect(stockRow).toBeVisible();
    await stockRow.click();

    // Verify AI Confidence chip is visible initially in AI Thesis section
    const confChip = page.locator('.ai-conf').first();
    await expect(confChip).toBeVisible();

    // Toggle tweaks panel: click the "AI confidence chips" custom switch button
    const tweaksToggle = page.locator('.twk-row:has-text("AI confidence chips") button.twk-toggle');
    await expect(tweaksToggle).toBeVisible();
    
    // Check initial state
    const initialState = await tweaksToggle.getAttribute('data-on');
    expect(initialState).toBe('1'); // Should be on initially

    // Click to turn off
    await tweaksToggle.click();

    // Verify that the document body has class 'qf-no-conf'
    const hasClass = await page.evaluate(() => document.body.classList.contains('qf-no-conf'));
    expect(hasClass).toBe(true);

    // Verify that the confidence chip is now hidden
    await expect(confChip).not.toBeVisible();

    // Click again to turn on
    await tweaksToggle.click();
    
    // Verify that the confidence chip is visible again
    await expect(confChip).toBeVisible();
  });
});
