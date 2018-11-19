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
        console.log('[select all populations]');
        const populationDropdown = By.xpath('//*[@id="ldpairForm"]/div[3]/div/div/button');
        await driver.findElement(populationDropdown).click();
        const populationALLCheckbox = By.xpath('//*[@id="ldpairForm"]/div[3]/div/div/ul/li[1]/a');
        await driver.findElement(populationALLCheckbox).click();
		// click calculate button
        console.log('[click calculate button]');
        const calculateButton = By.css('[id="ldpair"]');
        await driver.findElement(calculateButton).click();
        // assert warning message
        console.log('[assert if warning message is present]');
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
        resultsLinkageEquilibriumElementText.should.contain('rs2280548 and rs6984900 are in linkage equilibrium');
    });

    it('should display LDproxy results from a sample genomic query', async function() {
        console.log('test -> should display LDproxy results from a sample genomic query');
        const driver = this.driver;
        // switch to LDproxy tab
        console.log('[switch to LDproxy tab]');
        const tabLDproxy = By.css('[id="ldproxy-tab-anchor"]');
        await driver.wait(until.elementLocated(tabLDproxy));
        await driver.findElement(tabLDproxy).click();
        // input RS# rs2280548 into variant 1
        console.log('[input genomic coordinate chr22:25855459 into variant]');
        const variantInput = By.css('[id="ldproxy-snp"]');
        await driver.wait(until.elementLocated(variantInput));
        await driver.findElement(variantInput).sendKeys('chr22:25855459');
        // select population (AFR) African - (YRI) Yoruba in Ibadan, Nigeria
        console.log('[select population (AFR) African - (YRI) Yoruba in Ibadan, Nigeria]');
        const populationDropdown = By.xpath('//*[@id="ldproxyForm"]/div[2]/div/div/button');
        await driver.findElement(populationDropdown).click();
        const populationYRICheckbox = By.xpath('//*[@id="ldproxyForm"]/div[2]/div/div/ul/li[3]/a');
        await driver.findElement(populationYRICheckbox).click();
        // click calculate button once enabled
        console.log('[click calculate button once enabled]');
        const calculateButton = By.css('[id="ldproxy"]');
        const calculateButtonElement = driver.findElement(calculateButton);
        await driver.wait(until.elementIsEnabled(calculateButtonElement));
        await driver.findElement(calculateButton).click();
        // wait until Bokeh plot is visible
        console.log('[wait until Bokeh plot is visible]');
        const bokehPlot = By.css('[id="ldproxy-bokeh-graph"]');
        const bokehPlotElement = driver.findElement(bokehPlot);
        await driver.wait(until.elementIsVisible(bokehPlotElement));
        // wait until Bokeh Export plot button is enabled
        console.log('[wait until Bokeh Export plot button is enabled]');
        const exportPlotButton = By.css('[id="ldproxy-menu1"]');
        await driver.wait(until.elementLocated(exportPlotButton));
        const exportPlotButtonElement = driver.findElement(exportPlotButton);
        await driver.wait(until.elementIsEnabled(exportPlotButtonElement));
        // assert if Proxy Results table is present
        console.log('[assert if Proxy Results table is present]');
        const proxyResultsRSQuery = By.xpath('//*[@id="new-ldproxy"]/tbody/tr[1]/td[1]/a');
        await driver.wait(until.elementLocated(proxyResultsRSQuery));
        const proxyResultsRSQueryElement = driver.findElement(proxyResultsRSQuery);
        const proxyResultsRSQueryElementText = await proxyResultsRSQueryElement.getText();
        proxyResultsRSQueryElementText.should.contain('rs58892524');
    });

    // it('should display SNPchip results from sample file', async function() {
    //     console.log('test -> should display SNPchip results from sample file');
    //     const driver = this.driver;
    //     // switch to SNPchip tab
    //     console.log('[switch to SNPchip tab]');
    //     const tabSNPchip = By.css('[id="snpchip-tab-anchor"]');
    //     await driver.wait(until.elementLocated(tabSNPchip));
    //     await driver.findElement(tabSNPchip).click();
    //     // input SNPchip sample file with RS queries
    //     console.log('[input SNPchip sample file with RS queries]');
    //     const sampleFilePath = path.join(process.cwd(), 'tests','end-to-end', 'test-data', 'sample_SNPchip.txt');
    //     const fileInput = By.css('[id="snpchip-file"]');
    //     await driver.wait(until.elementLocated(fileInput));
    //     await driver.findElement(fileInput).sendKeys(sampleFilePath);
    //     // click calculate button
    //     console.log('[click calculate button]');
    //     const calculateButton = By.css('[id="snpchip"]');
    //     await driver.findElement(calculateButton).click();
    //     // assert RS # in thinned list
    //     console.log('[assert RS # in thinned list]');
    //     const tableRow = By.xpath('//*[@id="snpchip-thinned-list"]/tbody/tr[58]/td[1]');
    //     await driver.wait(until.elementLocated(tableRow));
    //     const tableRowElement = driver.findElement(tableRow);
    //     const tableRowElementText = await tableRowElement.getText();
    //     console.log(tableRowElementText);
    //     tableRowElementText.should.contain('rs11962771');
    //     // assert warning message
    //     console.log('[assert if warning message is present]');
    //     const warningAlert = By.xpath('//*[@id="snpchip-message-warning"]/div');
    //     const warningAlertElement = driver.findElement(warningAlert);
    //     const warningAlertElementText = await warningAlertElement.getText();
    //     warningAlertElementText.should.contain('The following RS number(s) or coordinate(s) were not found in dbSNP 151: rs562596074.');
    // });

    it('should display SNPclip results from sample file', async function() {
        console.log('test -> should display SNPchip results from sample file');
        const driver = this.driver;
        // switch to SNPclip tab
        console.log('[switch to SNPclip tab]');
        const tabSNPclip = By.css('[id="snpclip-tab-anchor"]');
        await driver.wait(until.elementLocated(tabSNPclip));
        await driver.findElement(tabSNPclip).click();
        // input SNPclip sample file with RS queries
        console.log('[input SNPclip sample file with RS queries]');
        const sampleFilePath = path.join(process.cwd(), 'tests','end-to-end', 'test-data', 'sample_SNPclip.txt');
        const fileInput = By.css('[id="snpclip-file"]');
        await driver.wait(until.elementLocated(fileInput));
        await driver.findElement(fileInput).sendKeys(sampleFilePath);
        // select population (AFR) African - (YRI) Yoruba in Ibadan, Nigeria
        console.log('[select population (AFR) African - (YRI) Yoruba in Ibadan, Nigeria]');
        const populationDropdown = By.xpath('//*[@id="snpclipForm"]/div[3]/div/button');
        await driver.findElement(populationDropdown).click();
        const populationYRICheckbox = By.xpath('//*[@id="snpclipForm"]/div[3]/div/ul/li[3]/a');
        await driver.findElement(populationYRICheckbox).click();
        // click calculate button
        console.log('[click calculate button]');
        const calculateButton = By.css('[id="snpclip"]');
        await driver.findElement(calculateButton).click();
        // wait until table is visible
        console.log('[wait until table is visible]');
        const table = By.xpath('//*[@id="snpclip-table-thin"]');
        const tableElement = driver.findElement(table);
        await driver.wait(until.elementIsVisible(tableElement));
        // assert warning message
        console.log('[assert if warning message is present]');
        const warningAlert = By.xpath('//*[@id="snpclip-message-warning-content"]');
        const warningAlertElement = driver.findElement(warningAlert);
        const warningAlertElementText = await warningAlertElement.getText();
        warningAlertElementText.should.contain('The following RS number(s) or coordinate(s) were not found in dbSNP 151: rs562596074.');
    });

    it('should display help text from separate html file', async function() {
        console.log('test -> should display help text from separate html file');
        const driver = this.driver;
        // switch to help tab
        console.log('[switch to help tab]');
        const tabHelp = By.css('[id="help-tab-anchor"]');
        await driver.wait(until.elementLocated(tabHelp));
        await driver.findElement(tabHelp).click();
        // wait until help tab is visible
        console.log('[wait until help tab is visible]');
        const tab = By.css('[id="help-tab"]');
        const tabElement = driver.findElement(tab);
        await driver.wait(until.elementIsVisible(tabElement));
        // assert description
        console.log('[assert description]');
        const helpDescription = By.xpath('//*[@id="help-tab"]/p[1]');
        const helpDescriptionElement = driver.findElement(helpDescription);
        const helpDescriptionElementText = await helpDescriptionElement.getText();
        helpDescriptionElementText.should.contain('LDlink is designed to be an intuitive and simple tool for investigating patterns of linkage disequilibrium across a variety of ancestral population groups. This help documentation page gives detailed description of the metrics calculated by LDlink modules and aids users in understanding all aspects of the required input and returned output. The documentation is divided into the following sections');
    });

    after(async function() {
        this.driver.quit();
    })
});