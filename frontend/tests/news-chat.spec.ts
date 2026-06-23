import { test, expect, type Page } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';

async function loginAndGoToDashboard(page: Page) {
  await page.goto(BASE_URL);
  await page.evaluate(() => localStorage.setItem('qf_auth', '1'));
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
}

test.describe('News & Chat Screen E2E Flows', () => {
  test('TC1: Màn hình Tin tức hiển thị đầy đủ bộ lọc mới (Loại tin, Ngành, Mã CK)', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Navigate to News Screen
    const newsLink = page.locator('.nav-link', { hasText: 'Tin tức' }).first();
    await expect(newsLink).toBeVisible();
    await newsLink.click();

    // Verify page title
    await expect(page.locator('.qf-pagehead h1')).toContainText('Dòng tin có gắn sentiment');

    // Verify segmented controls for sentiment, status, and new type filter
    await expect(page.locator('.grp button', { hasText: 'Tích cực' }).first()).toBeVisible();
    await expect(page.locator('.grp button', { hasText: 'Đã phân tích' }).first()).toBeVisible();
    await expect(page.locator('.grp button', { hasText: 'Tất cả loại tin' }).first()).toBeVisible();
    await expect(page.locator('.grp button', { hasText: 'Vĩ mô' }).first()).toBeVisible();
    await expect(page.locator('.grp button', { hasText: 'Doanh nghiệp' }).first()).toBeVisible();
    await expect(page.locator('.grp button', { hasText: 'Pháp lý' }).first()).toBeVisible();

    // Verify select elements for source, sector, and ticker
    const selectElements = page.locator('.filter-bar select');
    await expect(selectElements).toHaveCount(3);

    // Verify first options of select elements
    await expect(selectElements.nth(0).locator('option').first()).toHaveText('Mọi nguồn');
    await expect(selectElements.nth(1).locator('option').first()).toHaveText('Mọi ngành');
    await expect(selectElements.nth(2).locator('option').first()).toHaveText('Mọi mã CK');
  });

  test('TC2: Lọc tin tức hoạt động chính xác theo Loại tin, Ngành, Mã CK', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Navigate to News Screen
    await page.locator('.nav-link', { hasText: 'Tin tức' }).first().click();

    // Select "Doanh nghiệp" news type filter (which matches FPT)
    const bizButton = page.locator('.grp button', { hasText: 'Doanh nghiệp' }).first();
    await bizButton.click();

    // Verify news items are updated
    const countTextBefore = await page.locator('.filter-bar span').last().innerText();
    expect(countTextBefore).toContain('tin hiển thị');

    // Select specific sector (Công nghệ)
    const sectorSelect = page.locator('.filter-bar select').nth(1);
    await sectorSelect.selectOption({ label: 'Công nghệ' });

    // Select specific ticker (FPT)
    const tickerSelect = page.locator('.filter-bar select').nth(2);
    await tickerSelect.selectOption({ label: 'FPT' });

    // Verify filtered count is greater than 0
    const countTextAfter = await page.locator('.filter-bar span').last().innerText();
    expect(countTextAfter).toContain('tin hiển thị');
    const match = countTextAfter.match(/(\d+)/);
    expect(match).not.toBeNull();
    const count = parseInt(match![1], 10);
    expect(count).toBeGreaterThan(0);
  });

  test('TC3: Click vào ticker trong bài viết chuyển hướng sang Stock Detail', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Navigate to News Screen
    await page.locator('.nav-link', { hasText: 'Tin tức' }).first().click();

    // Reset filters to "Tất cả" to ensure items exist
    await page.locator('.grp button', { hasText: 'Tất cả' }).first().click();
    
    // Find the first ticker pill in news list
    const tickerPill = page.locator('.news-item .tickers .t-pill').first();
    await expect(tickerPill).toBeVisible();
    const tickerText = await tickerPill.innerText();

    // Click ticker pill
    await tickerPill.click();

    // Verify redirect to Stock Detail
    await expect(page.locator('.qf-pagehead h1')).toContainText(tickerText);
  });

  test('TC4: Màn hình Chat tải thành công, gửi tin nhắn nhận phản hồi mẫu', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Navigate to Chat Screen
    const chatLink = page.locator('.nav-link', { hasText: 'AI Chat' }).first();
    await expect(chatLink).toBeVisible();
    await chatLink.click();

    // Verify page header
    await expect(page.locator('h1', { hasText: 'Hỏi gì cũng được' })).toBeVisible();

    // Send a message
    const input = page.locator('input[placeholder*="Hỏi về cổ phiếu"]');
    await input.fill('Phân tích tiềm năng HPG');
    await input.press('Enter');

    // Verify user message is visible in stream
    await expect(page.locator('.msg.user', { hasText: 'Phân tích tiềm năng HPG' })).toBeVisible();

    // Verify AI response is loaded (automatically waits up to 5s)
    await expect(page.locator('.msg.ai').last()).toContainText('Phân tích chi tiết cho cổ phiếu HPG', { timeout: 5000 });
  });

  test('TC5: Click vào Ticker link trong AI response chuyển hướng sang Stock Detail', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Navigate to Chat Screen
    await page.locator('.nav-link', { hasText: 'AI Chat' }).first().click();

    // Check first default message from AI contains VHM links
    const tickerLink = page.locator('.msg.ai .ticker-link', { hasText: 'VHM' }).first();
    await expect(tickerLink).toBeVisible();

    // Click on VHM link
    await tickerLink.click();

    // Verify redirect to Stock Detail for VHM
    await expect(page.locator('.qf-pagehead h1')).toContainText('VHM');
  });
});
