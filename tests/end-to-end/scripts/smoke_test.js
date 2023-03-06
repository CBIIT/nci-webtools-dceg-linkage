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
            .setFirefoxOptions(new firefox.Options().headless()) // comment out to see browser locally
            .build();
        this.website = process.env.TEST_WEBSITE.replace(/\/$/, ''); // comment out to test locally
        // this.website = 'https://ldlink-dev.nih.gov/'; // comment in to test locally
    });

    it('should specify the correct website', async function() {
        console.log('test -> should specify the correct website');
        const driver = this.driver;
        await driver.get(this.website);
        console.log('[wait until title of HTML page contains LDlink]');
        await driver.wait(until.titleContains('LDlink'), 20000);
        console.log('[assert title of HTML page]');
        const title = await driver.getTitle();
        title.should.equal('LDlink | An Interactive Web Tool for Exploring Linkage Disequilibrium in Population Groups');
    });

    it('should display news text from separate html file', async function() {
        console.log('test -> should display news text from separate html file');
        const driver = this.driver;
        // wait until news and updates container is visible
        console.log('[wait until news and updates container is visible]');
        const newsContainer = By.css('[id="news-container"]');
        const newsContainerElement = driver.findElement(newsContainer);
        await driver.wait(until.elementIsVisible(newsContainerElement), 20000);
        // assert news text
        console.log('[assert news text]');
        const newsText = By.xpath('//*[@id="news-container"]');
        const newsTextElement = driver.findElement(newsText);
        const newsTextElementText = await newsTextElement.getText();
        newsTextElementText.should.contain('New features in');
    });

    it('should display LDassoc results from example GWAS data', async function() {
        console.log('test -> should display LDassoc results from example GWAS data');
        const driver = this.driver;
        // switch to LDassoc tab
        console.log('[switch to LDassoc tab]');
        const tabLDassoc = By.css('[id="ldassoc-tab-anchor"]');
        await driver.wait(until.elementLocated(tabLDassoc), 20000);
        await driver.findElement(tabLDassoc).click();
        // click Use example GWAS data
        console.log('[click Use example GWAS data]')
        const useExampleGWASbutton = By.xpath('//*[@id="ldassoc-sample"]/label/span');
        await driver.wait(until.elementLocated(useExampleGWASbutton), 20000);
        await driver.findElement(useExampleGWASbutton).click();
        // click calculate button once enabled
        console.log('[click calculate button once enabled]');
        const calculateButton = By.css('[id="ldassoc"]');
        const calculateButtonElement = driver.findElement(calculateButton);
        await driver.wait(until.elementIsEnabled(calculateButtonElement), 20000);
        await driver.findElement(calculateButton).click();
        // wait until Bokeh plot is visible
        console.log('[wait until Bokeh plot is visible]');
        const bokehPlot = By.css('[id="ldassoc-bokeh-graph"]');
        const bokehPlotElement = driver.findElement(bokehPlot);
        await driver.wait(until.elementIsVisible(bokehPlotElement), 20000);
        // wait until Bokeh Export plot button is enabled
        console.log('[wait until Bokeh Export plot button is enabled]');
        const exportPlotButton = By.css('[id="ldassoc-menu1"]');
        await driver.wait(until.elementLocated(exportPlotButton), 20000);
        const exportPlotButtonElement = driver.findElement(exportPlotButton);
        await driver.wait(until.elementIsEnabled(exportPlotButtonElement), 20000);
        // assert if Association Results table is present
        console.log('[assert if Association Results table is present]');
        const associationResultsRSQuery = By.xpath('//*[@id="new-ldassoc"]/tbody/tr[1]/td[1]/a');
        await driver.wait(until.elementLocated(associationResultsRSQuery), 20000);
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
        await driver.wait(until.elementLocated(tabLDhap), 20000);
        await driver.findElement(tabLDhap).click();
        // input LDhap sample file with RS and genomic coordinate queries
        console.log('[input LDhap sample file with RS and genomic coordinate queries]');
        const sampleFilePath = path.join(process.cwd(), 'tests','end-to-end', 'test-data', 'sample_LDhap.txt');
        const fileInput = By.css('[id="ldhap-file"]');
        await driver.wait(until.elementLocated(fileInput), 20000);
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
        await driver.wait(until.elementIsVisible(resultsTableElement), 20000);
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
        await driver.wait(until.elementLocated(tabLDmatrix), 20000);
        await driver.findElement(tabLDmatrix).click();
        // input LDmatrix sample file with RS queries
        console.log('[input LDmatrix sample file with RS queries]');
        const sampleFilePath = path.join(process.cwd(), 'tests','end-to-end', 'test-data', 'sample_LDmatrix.txt');
        const fileInput = By.css('[id="ldmatrix-file"]');
        await driver.wait(until.elementLocated(fileInput), 20000);
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
        await driver.wait(until.elementIsVisible(bokehPlotElement), 20000);
        // wait until Bokeh Export plot button is enabled
        console.log('[wait until Bokeh Export plot button is enabled]');
        const exportPlotButton = By.css('[id="ldmatrix-menu1"]');
        await driver.wait(until.elementLocated(exportPlotButton), 20000);
        const exportPlotButtonElement = driver.findElement(exportPlotButton);
        await driver.wait(until.elementIsEnabled(exportPlotButtonElement), 20000);
        // assert if LDmatrix R2 legend is present
        console.log('[assert if LDmatrix R2 legend is present]');
        const legend = By.css('[id="ldmatrix-legend-r2"]');
        await driver.wait(until.elementLocated(legend), 20000);
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
        await driver.wait(until.elementLocated(tabLDpair), 20000);
        await driver.findElement(tabLDpair).click();
        // input RS# rs2280548 into variant 1
        console.log('[input RS# rs2280548 into variant 1]');
        const variant1Input = By.css('[id="ldpair-snp1"]');
        await driver.wait(until.elementLocated(variant1Input), 20000);
        await driver.findElement(variant1Input).sendKeys('rs2280548');
        // input genomic coordinate chr8:128304269 into variant 2
        console.log('[input genomic coordinate chr8:128304269 into variant 2]');
        const variant2Input = By.css('[id="ldpair-snp2"]');
        await driver.wait(until.elementLocated(variant2Input), 20000);
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
        // console.log('[assert if warning message is present]');
        // const warningAlert = By.xpath('//*[@id="ldpair-message-warning"]/div');
        // const warningAlertElement = driver.findElement(warningAlert);
        // const warningAlertElementText = await warningAlertElement.getText();
        // warningAlertElementText.should.contain('rs2280548 and rs6984900 are on different chromosomes');
        // assert if results are in linkage equilibrium
        console.log('[assert if results are in linkage equilibrium]');
        const resultsTable = By.xpath('//*[@id="ldpair-results-container"]/table[1]');
        const resultsTableElement = driver.findElement(resultsTable);
        await driver.wait(until.elementIsVisible(resultsTableElement), 20000);
        const resultsLinkageEquilibrium = By.xpath('//*[@id="ldpair-results-container"]/div/div[1]');
        const resultsLinkageEquilibriumElement = driver.findElement(resultsLinkageEquilibrium);
        const resultsLinkageEquilibriumElementText = await resultsLinkageEquilibriumElement.getText();
        resultsLinkageEquilibriumElementText.should.contain('rs2280548 and rs6984900 are in linkage equilibrium');
    });

    it('should display LDpop results from a sample RS pair query', async function() {
        console.log('test -> should display LDpop results from a sample RS pair query');
        const driver = this.driver;
        // switch to LDpop tab
        console.log('[switch to LDpop tab]');
        const tabLDpair = By.css('[id="ldpop-tab-anchor"]');
        await driver.wait(until.elementLocated(tabLDpair), 20000);
        await driver.findElement(tabLDpair).click();
        // input RS# rs408825 into variant 1
        console.log('[input RS# rs408825 into variant 1]');
        const variant1Input = By.css('[id="ldpop-snp1"]');
        await driver.wait(until.elementLocated(variant1Input), 20000);
        await driver.findElement(variant1Input).sendKeys('rs408825');
        // input genomic coordinate rs398206 into variant 2
        console.log('[input genomic coordinate rs398206 into variant 2]');
        const variant2Input = By.css('[id="ldpop-snp2"]');
        await driver.wait(until.elementLocated(variant2Input), 20000);
        await driver.findElement(variant2Input).sendKeys('rs398206');
        // select all populations
        console.log('[select all populations]');
        const populationDropdown = By.xpath('//*[@id="ldpopForm"]/div[3]/div/div/button');
        await driver.findElement(populationDropdown).click();
        const populationALLCheckbox = By.xpath('//*[@id="ldpopForm"]/div[3]/div/div/ul/li[1]/a');
        await driver.findElement(populationALLCheckbox).click();
		// click calculate button
        console.log('[click calculate button]');
        const calculateButton = By.css('[id="ldpop"]');
        await driver.findElement(calculateButton).click();
        // assert if Google Maps API is being displayed
        console.log('[assert if Google Maps API is being displayed]');
        const mapAPI = By.xpath('//*[@id="map1"]');
        const mapAPIElement = driver.findElement(mapAPI);
        await driver.wait(until.elementIsVisible(mapAPIElement), 20000);
        // assert if results table is being displayed
        console.log('[assert if results table is being displayed]');
        const resultsTable = By.xpath('//*[@id="new-ldpop_wrapper"]');
        const resultsTableElement = driver.findElement(resultsTable);
        await driver.wait(until.elementIsVisible(resultsTableElement), 20000);
        const resultsShownEntries = By.xpath('//*[@id="new-ldpop_info_clone"]');
        const resultsShownEntriesElement = driver.findElement(resultsShownEntries);
        const rresultsShownEntriesElementText = await resultsShownEntriesElement.getText();
        rresultsShownEntriesElementText.should.contain('Showing 1 to 32 of 32 entries');
    });

    it('should display LDproxy results from a sample genomic query', async function() {
        console.log('test -> should display LDproxy results from a sample genomic query');
        const driver = this.driver;
        // switch to LDproxy tab
        console.log('[switch to LDproxy tab]');
        const tabLDproxy = By.css('[id="ldproxy-tab-anchor"]');
        await driver.wait(until.elementLocated(tabLDproxy), 20000);
        await driver.findElement(tabLDproxy).click();
        // input genomic coordinate chr22:25855459 into variant 1
        console.log('[input genomic coordinate chr22:25855459 into variant]');
        const variantInput = By.css('[id="ldproxy-snp"]');
        await driver.wait(until.elementLocated(variantInput), 20000);
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
        await driver.wait(until.elementIsEnabled(calculateButtonElement), 20000);
        await driver.findElement(calculateButton).click();
        // wait until Bokeh plot is visible
        console.log('[wait until Bokeh plot is visible]');
        const bokehPlot = By.css('[id="ldproxy-bokeh-graph"]');
        const bokehPlotElement = driver.findElement(bokehPlot);
        await driver.wait(until.elementIsVisible(bokehPlotElement), 30000);
        // wait until Bokeh Export plot button is enabled
        console.log('[wait until Bokeh Export plot button is enabled]');
        const exportPlotButton = By.css('[id="ldproxy-menu1"]');
        await driver.wait(until.elementLocated(exportPlotButton), 20000);
        const exportPlotButtonElement = driver.findElement(exportPlotButton);
        await driver.wait(until.elementIsEnabled(exportPlotButtonElement), 180000);
        // assert if Proxy Results table is present
        console.log('[assert if Proxy Results table is present]');
        const proxyResultsRSQuery = By.xpath('//*[@id="new-ldproxy"]/tbody/tr[1]/td[1]/a');
        await driver.wait(until.elementLocated(proxyResultsRSQuery), 20000);
        const proxyResultsRSQueryElement = driver.findElement(proxyResultsRSQuery);
        const proxyResultsRSQueryElementText = await proxyResultsRSQueryElement.getText();
        proxyResultsRSQueryElementText.should.contain('rs58892524');
    });

    it('should display SNPchip warning from sample file', async function() {
        console.log('test -> should display SNPchip results from sample file');
        const driver = this.driver;
        // switch to SNPchip tab
        console.log('[switch to SNPchip tab]');
        const tabSNPchip = By.css('[id="snpchip-tab-anchor"]');
        await driver.wait(until.elementLocated(tabSNPchip), 20000);
        await driver.findElement(tabSNPchip).click();
        // input SNPchip sample file with RS queries
        console.log('[input SNPchip sample file with RS queries]');
        const sampleFilePath = path.join(process.cwd(), 'tests','end-to-end', 'test-data', 'sample_SNPchip.txt');
        const fileInput = By.css('[id="snpchip-file"]');
        await driver.wait(until.elementLocated(fileInput), 20000);
        await driver.findElement(fileInput).sendKeys(sampleFilePath);
        // click calculate button
        console.log('[click calculate button]');
        const calculateButton = By.css('[id="snpchip"]');
        await driver.findElement(calculateButton).click();
        // wait until warning message is located
        console.log('[wait until warning message is located]');
        const warningMessage = By.css('[id="snpchip-message-warning-content"]');
        await driver.wait(until.elementLocated(warningMessage), 20000);
    });

    it('should display SNPclip results from sample file', async function() {
        console.log('test -> should display SNPclip results from sample file');
        const driver = this.driver;
        // switch to SNPclip tab
        console.log('[switch to SNPclip tab]');
        const tabSNPclip = By.css('[id="snpclip-tab-anchor"]');
        await driver.wait(until.elementLocated(tabSNPclip), 20000);
        await driver.findElement(tabSNPclip).click();
        // input SNPclip sample file with RS queries
        console.log('[input SNPclip sample file with RS queries]');
        const sampleFilePath = path.join(process.cwd(), 'tests','end-to-end', 'test-data', 'sample_SNPclip.txt');
        const fileInput = By.css('[id="snpclip-file"]');
        await driver.wait(until.elementLocated(fileInput), 20000);
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
        await driver.wait(until.elementIsVisible(tableElement), 20000);
        // assert warning message
        console.log('[assert if warning message is present]');
        const warningAlert = By.xpath('//*[@id="snpclip-message-warning-content"]');
        const warningAlertElement = driver.findElement(warningAlert);
        const warningAlertElementText = await warningAlertElement.getText();
        warningAlertElementText.should.contain('Genomic position for query variant (rs536475674) does not match RS number at 1000G position (chr6:5687279). Genomic position for query variant (rs544061638) does not match RS number at 1000G position (chr6:18252763). Genomic position for query variant (rs562596074) does not match RS number at 1000G position (chr6:22075527). Genomic position for query variant (rs6915408) does not match RS number at 1000G position (chr6:29763303)');
    });

    it('should display help text from separate html file', async function() {
        console.log('test -> should display help text from separate html file');
        const driver = this.driver;
        // switch to help tab
        console.log('[switch to help tab]');
        const tabHelp = By.css('[id="help-tab-anchor"]');
        await driver.wait(until.elementLocated(tabHelp), 20000);
        await driver.findElement(tabHelp).click();
        // wait until help tab is visible
        console.log('[wait until help tab is visible]');
        const tab = By.css('[id="help-tab"]');
        const tabElement = driver.findElement(tab);
        await driver.wait(until.elementIsVisible(tabElement), 20000);
        // assert description
        console.log('[assert description]');
        const helpDescription = By.xpath('//*[@id="help-tab"]/p[1]');
        const helpDescriptionElement = driver.findElement(helpDescription);
        const helpDescriptionElementText = await helpDescriptionElement.getText();
        helpDescriptionElementText.should.contain('LDlink is designed to be an intuitive and simple tool for investigating patterns of linkage disequilibrium across a variety of ancestral population groups. This help documentation page gives detailed description of the metrics calculated by LDlink modules and aids users in understanding all aspects of the required input and returned output. The documentation is divided into the following sections');
    });

    it('should check if user is already registed in API Access tab', async function() {
        console.log('test -> should check if user is already registed in API Access tab');
        const driver = this.driver;
        // switch to help tab
        console.log('[switch to apiaccess tab]');
        const tabAPIaccess = By.css('[id="apiaccess-tab-anchor"]');
        await driver.wait(until.elementLocated(tabAPIaccess), 20000);
        await driver.findElement(tabAPIaccess).click();
        // wait until first name input field is visible
        console.log('[wait until first name input field is located]');
        const firstnameInput = By.css('[id="apiaccess-firstname"]');
        const firstnameInputElement = driver.findElement(firstnameInput);
        await driver.wait(until.elementIsVisible(firstnameInputElement), 20000);
        // input "Kevin" into first name input field
        console.log('[input "Kevin" into first name input field]');
        await driver.findElement(firstnameInput).sendKeys('Kevin');
        // input "Jiang" into first name input field
        console.log('[input "Jiang" into last name input field]');
        const lastnameInput = By.css('[id="apiaccess-lastname"]');
        await driver.findElement(lastnameInput).sendKeys('Jiang');
        // input "kevin.jiang2@nih.gov" into email input field
        console.log('[input "kevin.jiang2@nih.gov" into last name input field]');
        const emailInput = By.css('[id="apiaccess-email"]');
        await driver.findElement(emailInput).sendKeys('kevin.jiang2@nih.gov');
        // input "NCI" into test input field
        console.log('[input "NCI" into last name input field]');
        const institutionInput = By.css('[id="apiaccess-institution"]');
        await driver.findElement(institutionInput).sendKeys('NCI');
        // click submit button
        console.log('[click submit button]');
        const submitButton = By.css('[id="apiaccess"]');
        await driver.findElement(submitButton).click();
        // wait until warning modal is visible for new user
        console.log('[wait warning modal is visible for new user]');
        try {
            const warningModalNew = By.css('[id="apiaccess-new-user"]');
            const warningModalNewElement = driver.findElement(warningModalNew);
            await driver.wait(until.elementIsVisible(warningModalNewElement), 3000);
            // assert modal title
            console.log('[assert modal title]');
            const modalTitle = By.xpath('//*[@id="apiaccess-new-user"]/div/div/div[1]');
            const modalTitleElement = driver.findElement(modalTitle);
            const modalTitleElementText = await modalTitleElement.getText();
            modalTitleElementText.should.contain('Thank you for registering to use the LDlink API.');
        } catch (e) {
            console.log("[user is not new]");
        }
        
        // wait until warning modal is visible for existing user
        console.log('[wait warning modal is visible for existing user]');
        try {
            const warningModalExisting = By.css('[id="apiaccess-existing-user"]');
            const warningModalExistingElement = driver.findElement(warningModalExisting);
            await driver.wait(until.elementIsVisible(warningModalExistingElement), 3000);
            // assert modal title
            console.log('[assert modal title]');
            const modalTitle = By.xpath('//*[@id="apiaccess-existing-user"]/div/div/div[1]');
            const modalTitleElement = driver.findElement(modalTitle);
            const modalTitleElementText = await modalTitleElement.getText();
            modalTitleElementText.should.contain('Email already registered.');
        } catch(e) {
            console.log("[user is not existing]");
        }
        // wait until warning modal is visible for blocked user
        console.log('[wait warning modal is visible for blocked user]');
        try {
            const warningModalBlocked = By.css('[id="apiaccess-blocked-user"]');
            const warningModalBlockedElement = driver.findElement(warningModalBlocked);
            await driver.wait(until.elementIsVisible(warningModalBlockedElement), 3000);
            // assert modal title
            console.log('[assert modal title]');
            const modalTitle = By.xpath('//*[@id="apiaccess-blocked-user"]/div/div/div[1]');
            const modalTitleElement = driver.findElement(modalTitle);
            const modalTitleElementText = await modalTitleElement.getText();
            modalTitleElementText.should.contain('Your email is associated with a blocked API token.');
        } catch(e) {
            console.log("[user is not blocked]");
        }
    });

    after(async function() {
        this.driver.quit();
    })
});