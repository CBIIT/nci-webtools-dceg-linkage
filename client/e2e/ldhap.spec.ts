import { test, expect } from '@playwright/test';

test.describe('LDHap Page', () => {
  test('should load the LDHap page and display the main content, submit SNPs and population, and verify results', async ({ page }) => {
    await page.goto('http://localhost:808/ldhap');
    // Fail the test if a 404 error is shown
    const is404 = await page.locator('h1', { hasText: '404' }).count();
    expect(is404).toBe(0);
    // Check for a main heading or unique element on the LDHap page
    await expect(page.locator('h1, h2, [data-testid="ldhap-main"]')).toBeVisible();

    // Enter SNPs
    await page.fill('textarea[name="snps"]', 'rs3\nrs4');

    // Select population 'YRI' using react-select
    await page.click('.select__control'); // open the dropdown
    await page.getByText('YRI').click(); // click the YRI option

    // Submit the form (assuming a button with type submit or data-testid)
    await page.click('button[type="submit"], [data-testid="ldhap-submit"]');

    // Wait for results to load (assuming a results table or unique result element)
    await expect(page.locator('[data-testid="ldhap-results"]')).toBeVisible({ timeout: 10000 });

    // Optionally, check that results contain expected SNPs
    const resultsText = await page.locator('[data-testid="ldhap-results"]').textContent();
    expect(resultsText).toContain('rs3');
    expect(resultsText).toContain('rs4');
  });

  test('should render haplotype colors matching their corresponding letters', async ({ page }) => {
    await page.goto('http://localhost:808/ldhap');
    // Enter SNPs and select population as in the main test
    await page.fill('textarea[name="snps"]', 'rs3\nrs4');
    await page.click('.select__control');
    await page.getByText('YRI').click();
    await page.click('button[type="submit"], [data-testid="ldhap-submit"]');
    await expect(page.locator('[data-testid="ldhap-results"]')).toBeVisible({ timeout: 10000 });

    // Check haplotype table cells for correct color classes
    const hapCells = await page.locator('#ldhap-table-right td.haplotype').all();
    for (const cell of hapCells) {
      const textRaw = await cell.textContent();
      const text = textRaw?.trim().toLowerCase();
      if (text && ["a", "t", "c", "g", "-"].includes(text)) {
        const classList = await cell.getAttribute('class');
        if (text === '-') {
          expect(classList).toContain('haplotype_dash');
        } else {
          expect(classList).toContain(`haplotype_${text}`);
        }
      }
    }
  });
});
