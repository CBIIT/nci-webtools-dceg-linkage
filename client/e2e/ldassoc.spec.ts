import { test, expect } from '@playwright/test'

test('should display LDassoc results from example GWAS data', async ({ page }) => {
  await page.goto('http://localhost:808/ldassoc');

  // click Use example GWAS data
  await page.getByLabel('Use example GWAS data').check();

  // click calculate button
  await page.getByTestId('calculate-button').click();

  // wait 15 seconds after clicking calculate
  await page.waitForTimeout(15000);

//   check for Association Results heading
  await expect(page.getByRole('heading', { name: 'Association Results', level: 4 })).toBeVisible();

  // wait until Bokeh plot is visible
  await expect(page.locator('div#plot')).toBeVisible({ timeout: 20000 });

  // wait until Bokeh Export plot button is enabled
  await expect(page.getByRole('button', { name: 'Export' })).toBeEnabled({ timeout: 20000 });

  // assert if Association Results table is present and contains the correct data
  await expect(page.getByRole('cell', { name: 'rs7837688' })).toBeVisible();
});