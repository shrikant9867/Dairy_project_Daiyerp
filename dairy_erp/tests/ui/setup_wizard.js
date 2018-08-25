console.log("inside tests ui dairyb erp")

module.exports = {
	before: browser => {
		browser
			.url(browser.launch_url + '/login')
			.waitForElementVisible('body', 5000);
	},	
	'Configuration': browser => {
		let slide_selector = '[data-slide-name="dairy_erp_configuration"]';
		browser
			.waitForElementVisible(slide_selector, 2000)
			.click(slide_selector + ' .next-btn');
	},
	after: browser => {
		browser.end();
	},
};