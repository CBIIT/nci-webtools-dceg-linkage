const should = require('chai').should();

describe('Environmental Variables', function() {
    it('should specify the website in the TEST_WEBSITE environmental variable', function() {
        console.log('test -> should specify the website in the TEST_WEBSITE environmental variable');
        const value = process.env.TEST_WEBSITE;
        console.log('[check to see if the environmental variable TEST_WEBSITE is injected]')
        should.exist(value);
        value.should.be.a('string');
        value.should.not.be.empty;
    });
});