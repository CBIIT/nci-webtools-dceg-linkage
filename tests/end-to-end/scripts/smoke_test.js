const path = require('path');
const request = require('request');
const should = require('chai').should();
const { expect } = require('chai');
const { Builder, By, Key, until } = require('selenium-webdriver');
const firefox = require('selenium-webdriver/firefox');

describe('LDlink Smoke Test', function() {
    this.timeout(0);

    before(async function() {
        this.driver = await new Builder()
            .forBrowser('firefox')
            .setFirefoxOptions(new firefox.Options().headless())
            .build();
        // this.website = process.env.TEST_WEBSITE.replace(/\/$/, '');
        this.website = 'https://ldlink-dev.nci.nih.gov/';
    });

    it('should specify the correct website', async function() {
        const driver = this.driver;
        await driver.get(this.website);
        await driver.wait(until.titleContains('LDlink'));
        const title = await driver.getTitle();
        title.should.equal('LDlink | An Interactive Web Tool for Exploring Linkage Disequilibrium in Population Groups');
    });

    it('should display LDassoc example GWAS data', async function() {
        const driver = this.driver;
        // switch to LDassoc tab
        console.log('[switch to LDassoc tab]');
        const tabLDassoc = By.css('[id="ldassoc-tab-anchor"]');
        await driver.wait(until.elementLocated(tabLDassoc));
        await driver.findElement(tabLDassoc).click();
        // click Use example GWAS data
        console.log('[click Use example GWAS data]')
        const useExampleGWASbutton = By.xpath('//*[@id="ldassoc-sample"]/label/span');
        await driver.wait(until.elementLocated(useExampleGWASbutton));
        await driver.findElement(useExampleGWASbutton).click();
        // click calculate button once enabled
        console.log('[click calculate button once enabled]');
        const calculateButton = By.css('[id="ldassoc"]');
        const calculateButtonElement = driver.findElement(calculateButton);
        await driver.wait(until.elementIsEnabled(calculateButtonElement));
        await driver.findElement(calculateButton).click();
        // wait until Bokeh plot is visible
        // const bokehPlot = By.css('[id="ldassoc-bokeh-graph"]');
        // const bokehPlotElement = driver.findElement(bokehPlot);
        // await driver.wait(until.elementIsVisible(bokehPlotElement));
        // wait until Bokeh Export plot button is enabled
        const exportPlotButton = By.css('[id="ldassoc-menu1"]');
        await driver.wait(until.elementLocated(exportPlotButton));
        const exportPlotButtonElement = driver.findElement(exportPlotButton);
        await driver.wait(until.elementIsEnabled(exportPlotButtonElement));
        // assert if Association Results table is present
        console.log('[assert if Association Results table is present]');
        const associationResultsTable = By.css('[id="new-ldassoc"]');
        await driver.wait(until.elementLocated(associationResultsTable));
        const associationResultsTableElement = driver.findElement(associationResultsTable);
        const associationResultsTableClass = await associationResultsTableElement.getAttribute('class');
        associationResultsTableClass.should.contain('dataTable');
    });

    after(async function() {
        this.driver.quit();
    })
});