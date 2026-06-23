import { test, expect, type Page } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';

async function loginAndGoToDashboard(page: Page) {
  await page.goto(BASE_URL);
  await page.evaluate(() => localStorage.setItem('qf_auth', '1'));
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
}

test.describe('Alerts & Settings Screen E2E Flows', () => {
  test('TC1: Alerts flow - xem danh sách, đóng cảnh báo cập nhật SideRail badge, xem chi tiết modal và tạo rule mới', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Click "Cảnh báo" link on SideRail
    const alertsNavLink = page.locator('.nav-link', { hasText: 'Cảnh báo' }).first();
    await expect(alertsNavLink).toBeVisible();
    await alertsNavLink.click();

    // Verify redirected to Alerts page
    await expect(page.locator('.qf-pagehead h1')).toContainText('Cảnh báo & kênh phân phối');

    // Tab segment check: Lịch sử (history) tab is active initially
    const tabHistory = page.locator('.seg', { hasText: 'Lịch sử' }).first();
    await expect(tabHistory).toBeVisible();
    await expect(tabHistory).toHaveAttribute('data-active', 'true');

    // Verify alert list has items
    const alertRow = page.locator('.alert-row').first();
    await expect(alertRow).toBeVisible();

    // Get current badge count on SideRail
    const badge = alertsNavLink.locator('span').nth(1); // the badge span
    let initialCount = 0;
    if (await badge.isVisible()) {
      initialCount = parseInt(await badge.innerText());
    }

    // Click xem chi tiết alert row
    await alertRow.click();
    
    // Expect detail modal to be visible
    const detailModal = page.locator('text=Chi tiết Cảnh báo');
    await expect(detailModal).toBeVisible();
    
    // Click "Đồng ý" to close modal
    await page.locator('button', { hasText: 'Đồng ý' }).click();
    await expect(detailModal).not.toBeVisible();

    // Now click the dismiss button on the first alert row
    const dismissBtn = alertRow.locator('button[aria-label="Dismiss alert"]').first();
    await expect(dismissBtn).toBeVisible();
    await dismissBtn.click();

    // Verify SideRail badge count decreased
    if (initialCount > 0) {
      await expect(badge).toHaveText((initialCount - 1).toString());
    }

    // Go to Rules tab
    const tabRules = page.locator('.seg', { hasText: 'Rules' }).first();
    await expect(tabRules).toBeVisible();
    await tabRules.click();
    await expect(tabRules).toHaveAttribute('data-active', 'true');

    // Click "Tạo rule mới" button
    const createRuleBtn = page.locator('button', { hasText: 'Tạo rule mới' }).first();
    await expect(createRuleBtn).toBeVisible();
    await createRuleBtn.click();

    // Expect Create Rule Modal to show
    const createModal = page.locator('text=Tạo Quy tắc Cảnh báo mới');
    await expect(createModal).toBeVisible();

    // Fill the rule form
    await page.fill('.qf-input-field', 'Test Alert Rule VIC');
    await page.selectOption('.qf-select-field', 'price');
    await page.fill('.qf-ticker-input', 'VIC');
    await page.selectOption('.qf-operator-select', '>');
    await page.fill('.qf-threshold-input', '48000');
    
    // Submit
    await page.locator('button[type="submit"]').click();
    await expect(createModal).not.toBeVisible();

    // Verify new rule is prepended/present in the list
    await expect(page.locator('text=Test Alert Rule VIC')).toBeVisible();
  });

  test('TC2: Settings flow - điều hướng settings menu, thay đổi cấu hình LLM Gateway, test connection, và lưu', async ({ page }) => {
    await loginAndGoToDashboard(page);

    // Click "Cài đặt" link on SideRail
    const settingsNavLink = page.locator('.nav-link', { hasText: 'Cài đặt' }).first();
    await expect(settingsNavLink).toBeVisible();
    await settingsNavLink.click();

    // Verify Settings screen loaded
    await expect(page.locator('.qf-pagehead h1')).toContainText('Cấu hình hệ thống');

    // LHS nav groups check
    await expect(page.locator('.set-nav-grp-label', { hasText: 'AI & Dữ liệu' })).toBeVisible();
    await expect(page.locator('.set-nav-grp-label', { hasText: 'Giao diện' })).toBeVisible();
    await expect(page.locator('.set-nav-grp-label', { hasText: 'Thông báo' })).toBeVisible();
    await expect(page.locator('.set-nav-grp-label', { hasText: 'Tài khoản' })).toBeVisible();
    await expect(page.locator('.set-nav-grp-label', { hasText: 'Nâng cao' })).toBeVisible();

    // Check LLM Gateway is active
    const llmNavItem = page.locator('.set-nav-item', { hasText: 'LLM Gateway' }).first();
    await expect(llmNavItem).toHaveAttribute('data-active', 'true');

    // Verify LLM Gateway inputs
    const endpointInput = page.locator('.qf-endpoint-input');
    const apikeyInput = page.locator('.qf-apikey-input');
    await expect(endpointInput).toBeVisible();
    await expect(apikeyInput).toBeVisible();

    // Test connection with empty inputs should show error
    await endpointInput.fill('');
    await apikeyInput.fill('');
    await page.click('.qf-test-conn-btn');
    await expect(page.locator('.qf-test-error')).toContainText('không được trống');

    // Fill valid endpoints and api key
    await endpointInput.fill('https://api.openai.com/v1');
    await apikeyInput.fill('sk-proj-testkey1234567890');
    
    // Test connection simulation success
    await page.click('.qf-test-conn-btn');
    await expect(page.locator('.qf-test-success')).toContainText('Kết nối thành công');

    // Update model dropdown and temperature slider
    await page.selectOption('.qf-model-select', 'gpt4o');
    await page.fill('.qf-temp-slider', '0.7');

    // Save changes
    const saveBtn = page.locator('button', { hasText: 'Lưu thay đổi' }).first();
    await expect(saveBtn).toBeVisible();
    await saveBtn.click();

    // Verify qf_llm_model and qf_llm_temp are updated in localStorage
    const savedModel = await page.evaluate(() => localStorage.getItem('qf_llm_model'));
    const savedTemp = await page.evaluate(() => localStorage.getItem('qf_llm_temp'));
    expect(savedModel).toBe('gpt4o');
    expect(savedTemp).toBe('0.7');
  });
});
