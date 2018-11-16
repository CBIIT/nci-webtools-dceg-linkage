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

    it('should display LDpair results from a sample RS and genomic coordinate query', async function() {
        console.log('test -> should display LDpair results from a sample RS and genomic coordinate query');
        const driver = this.driver;
        // switch to LDpair tab
        console.log('[switch to LDpair tab]');
        const tabLDpair = By.css('[id="ldpair-tab-anchor"]');
        await driver.wait(until.elementLocated(tabLDpair));
        await driver.findElement(tabLDpair).click();
        // input RS# rs2280548 into variant 1
        console.log('[input RS# rs2280548 into variant 1]');
        const variant1Input = By.css('[id="ldpair-snp1"]');
        await driver.wait(until.elementLocated(variant1Input));
        await driver.findElement(variant1Input).sendKeys('rs2280548');
        // input genomic coordinate chr8:128304269 into variant 2
        console.log('[input genomic coordinate chr8:128304269 into variant 2]');
        const variant2Input = By.css('[id="ldpair-snp2"]');
        await driver.wait(until.elementLocated(variant2Input));
        await driver.findElement(variant2Input).sendKeys('chr8:128304269');
        // select all populations
        console.log('[select all populations');
        const populationDropdown = By.xpath('//*[@id="ldpairForm"]/div[3]/div/div/button');
        await driver.findElement(populationDropdown).click();
        const populationALLCheckbox = By.xpath('//*[@id="ldpairForm"]/div[3]/div/div/ul/li[1]/a');
        await driver.findElement(populationALLCheckbox).click();
		// click calculate button
        console.log('[click calculate button]');
        const calculateButton = By.css('[id="ldpair"]');
        await driver.findElement(calculateButton).click();
        // assert warning message
        console.log('[assert if warning message is present');
        const warningAlert = By.xpath('//*[@id="ldpair-message-warning"]/div');
        const warningAlertElement = driver.findElement(warningAlert);
        const warningAlertElementText = await warningAlertElement.getText();
        warningAlertElementText.should.contain('rs2280548 and rs6984900 are on different chromosomes');
        // assert if results are in linkage equilibrium
        console.log('[assert if results are in linkage equilibrium]');
        const resultsTable = By.xpath('//*[@id="ldpair-results-container"]/table[1]');
        const resultsTableElement = driver.findElement(resultsTable);
        await driver.wait(until.elementIsVisible(resultsTableElement));
        const resultsLinkageEquilibrium = By.xpath('//*[@id="ldpair-results-container"]/div/div');
        const resultsLinkageEquilibriumElement = driver.findElement(resultsLinkageEquilibrium);
        const resultsLinkageEquilibriumElementText = await resultsLinkageEquilibriumElement.getText();
        console.log(resultsLinkageEquilibriumElementText);
        resultsLinkageEquilibriumElementText.should.contain('rs2280548 and rs6984900 are in linkage equilibrium');
    });

    after(async function() {
        this.driver.quit();
    })
});