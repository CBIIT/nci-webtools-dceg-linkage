
const assert = require('assert');
const path = require('path');
const test = require('selenium-webdriver/testing');
const webdriver = require('selenium-webdriver'),
By = webdriver.By,
until = webdriver.until;

describe('Test Suite 1 - ' + path.basename(__filename), function() {
  // default: {filename} - Test Suite 1

  test.before(function(){
        
    // do something before test suite execution
    // no matter if there are failed cases

  });

  test.after(function(){

    // do something after test suite execution is finished
    // no matter if there are failed cases

  });

  test.beforeEach(function(){
    
    // do something before test case execution
    // no matter if there are failed cases

  });

  test.afterEach(function(){

    // do something after test case execution is finished
    // no matter if there are failed cases

  });

  test.it('LDhap_Test', function(done) {
    this.timeout(0);
    var driver = new webdriver.Builder()
    .forBrowser('chrome')
    .build();

    // -----example get path of example test file----- 
    // --enter name of example input files folder in main directory (ie. 'examples')  
    // let examplesDirectory = __dirname.split(path.sep).concat(['examples']);

    // --enter name of file (ie. 'study2.txt')
    // driver.findElement(By.id("study_1")).sendKeys(examplesDirectory.concat(['study2.txt']).join(path.sep)).then(function() {
    //   driver.sleep(1000);
    // });

    driver.get("https://ldlink-dev.nci.nih.gov" + "/");
		driver.sleep('2000');
		driver.findElement(By.id(`ldhap-tab-anchor`)).click();
		driver.sleep('2000');
		driver.findElement(By.id(`ldhap-file`)).sendKeys('/home/ncianalysis/.jenkins/jobs/LDlink-sandbox-testing-only/workspace/test/end-to-end/test-data/5_sample_LDhap.txt');
		driver.sleep('2000');
		driver.findElement(By.xpath(`(//button[@type='button'])[6]`)).click();
		driver.sleep('2000');
		driver.findElement(By.xpath(`//form[@id='ldhapForm']/div[3]/div/div/ul/li[3]/a/label`)).click();
		driver.sleep('2000');
		driver.findElement(By.id(`ldhap`)).click();
		driver.sleep('3000');
		driver.findElement(By.css(`a[title="Cluster Report"] > span`)).getText().then(text=> {
			assert(text == 'rs2182115');
			done();
		});
		

    driver.close();
  });

  // test.it("Test-2", function(done){
 
  //   // test Code
  //   // assertions
    
  // });

  // test.it("Test-3", function(done){

  //     // test Code
  //     // assertions

  // });

})
