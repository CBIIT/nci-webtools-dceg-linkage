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
        this.website = process.env.TEST_WEBSITE.replace(/\/$/, '');
        // this.website = 'https://ldlink-dev.nci.nih.gov/';
    });

    it('should specify the correct website', async function() {
        console.log('test -> should specify the correct website');
        const driver = this.driver;
        await driver.get(this.website);
        console.log('[wait until title of HTML page contains LDlink]');
        await driver.wait(until.titleContains('LDlink'));
        console.log('[assert title of HTML page]');
        const title = await driver.getTitle();
        title.should.equal('LDlink | An Interactive Web Tool for Exploring Linkage Disequilibrium in Population Groups');
    });

    it('should display LDassoc results from example GWAS data', async function() {
        console.log('test -> should display LDassoc results from example GWAS data');
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
        console.log('[wait until Bokeh plot is visible]');
        const bokehPlot = By.css('[id="ldassoc-bokeh-graph"]');
        const bokehPlotElement = driver.findElement(bokehPlot);
        await driver.wait(until.elementIsVisible(bokehPlotElement));
        // wait until Bokeh Export plot button is enabled
        console.log('[wait until Bokeh Export plot button is enabled]');
        const exportPlotButton = By.css('[id="ldassoc-menu1"]');
        await driver.wait(until.elementLocated(exportPlotButton));
        const exportPlotButtonElement = driver.findElement(exportPlotButton);
        await driver.wait(until.elementIsEnabled(exportPlotButtonElement));
        // assert if Association Results table is present
        console.log('[assert if Association Results table is present]');
        const associationResultsRSQuery = By.xpath('//*[@id="new-ldassoc"]/tbody/tr[1]/td[1]/a');
        await driver.wait(until.elementLocated(associationResultsRSQuery));
        const associationResultsRSQueryElement = driver.findElement(associationResultsRSQuery);
        const associationResultsRSQueryElementText = await associationResultsRSQueryElement.getText();
        associationResultsRSQueryElementText.should.contain('rs7837688');
    });

    it('should display LDhap results from sample file with RS and genomic coordinate queries', async function() {
        console.log('test -> should display LDhap results from sample file with RS and genomic coordinate queries');
        const driver = this.driver;
        // switch to LDhap tab
        console.log('[switch to LDhap tab]');
        const tabLDhap = By.css('[id="ldhap-tab-anchor"]');
        await driver.wait(until.elementLocated(tabLDhap));
        await driver.findElement(tabLDhap).click();
        // input LDhap sample file with RS and genomic coordinate queries
        console.log('[input LDhap sample file with RS and genomic coordinate queries]');
        const sampleFilePath = path.join(process.cwd(), 'tests','end-to-end', 'test-data', 'sample_LDhap.txt');
        const fileInput = By.css('[id="ldhap-file"]');
        await driver.wait(until.elementLocated(fileInput));
        await driver.findElement(fileInput).sendKeys(sampleFilePath);
        // select population (AFR) African - (YRI) Yoruba in Ibadan, Nigeria
        console.log('[select population (AFR) African - (YRI) Yoruba in Ibadan, Nigeria]');
        const populationDropdown = By.xpath('//*[@id="ldhapForm"]/div[3]/div/div/button');
        await driver.findElement(populationDropdown).click();
        const populationYRICheckbox = By.xpath('//*[@id="ldhapForm"]/div[3]/div/div/ul/li[3]/a');
        await driver.findElement(populationYRICheckbox).click();
		// click calculate button
        console.log('[click calculate button]');
        const calculateButton = By.css('[id="ldhap"]');
        await driver.findElement(calculateButton).click();
        // assert if Association Results table is present
        console.log('[assert if Association Results table is present]');
        const resultsTable = By.xpath('//*[@id="ldhap-results-container"]/div');
        const resultsTableElement = driver.findElement(resultsTable);
        await driver.wait(until.elementIsVisible(resultsTableElement));
        const haplotypeFrequency = By.xpath('//*[@id="ldhap-table-right"]/tfoot/tr[2]/td[1]');
        const haplotypeFrequencyElement = driver.findElement(haplotypeFrequency);
        const haplotypeFrequencyResults = await haplotypeFrequencyElement.getText();
        haplotypeFrequencyResults.should.contain('0.8565');
    });

    it('should display LDmatrix results from sample file', async function() {
        console.log('test -> should display LDmatrix results from sample file');
        const driver = this.driver;
        // switch to LDmatrix tab
        console.log('[switch to LDmatrix tab]');
        const tabLDmatrix = By.css('[id="ldmatrix-tab-anchor"]');
        await driver.wait(until.elementLocated(tabLDmatrix));
        await driver.findElement(tabLDmatrix).click();
        // input LDmatrix sample file with RS queries
        console.log('[input LDmatrix sample file with RS queries]');
        const sampleFilePath = path.join(process.cwd(), 'tests','end-to-end', 'test-data', 'sample_LDmatrix.txt');
        const fileInput = By.css('[id="ldmatrix-file"]');
        await driver.wait(until.elementLocated(fileInput));
        await driver.findElement(fileInput).sendKeys(sampleFilePath);
        // select population (AFR) African - (YRI) Yoruba in Ibadan, Nigeria
        console.log('[select population (AFR) African - (YRI) Yoruba in Ibadan, Nigeria]');
        const populationDropdown = By.xpath('//*[@id="ldmatrixForm"]/div[2]/div/div/button');
        await driver.findElement(populationDropdown).click();
        const populationYRICheckbox = By.xpath('//*[@id="ldmatrixForm"]/div[2]/div/div/ul/li[3]/a');
        await driver.findElement(populationYRICheckbox).click();
        // click calculate button
        console.log('[click calculate button]');
        const calculateButton = By.css('[id="ldmatrix"]');
        await driver.findElement(calculateButton).click();
        // wait until Bokeh plot is visible
        console.log('[wait until Bokeh plot is visible]');
        const bokehPlot = By.css('[id="ldmatrix-bokeh-graph"]');
        const bokehPlotElement = driver.findElement(bokehPlot);
        await driver.wait(until.elementIsVisible(bokehPlotElement));
        // wait until Bokeh Export plot button is enabled
        console.log('[wait until Bokeh Export plot button is enabled]');
        const exportPlotButton = By.css('[id="ldmatrix-menu1"]');
        await driver.wait(until.elementLocated(exportPlotButton));
        const exportPlotButtonElement = driver.findElement(exportPlotButton);
        await driver.wait(until.elementIsEnabled(exportPlotButtonElement));
        // assert if LDmatrix R2 legend is present
        console.log('[assert if LDmatrix R2 legend is present]');
        const legend = By.css('[id="ldmatrix-legend"]');
        await driver.wait(until.elementLocated(legend));
        const legendElement = driver.findElement(legend);
        const legendSrc = await legendElement.getAttribute('src');
        legendSrc.should.contain('LDmatrix_legend_R2.png');
    });

    after(async function() {
        this.driver.quit();
    })
});