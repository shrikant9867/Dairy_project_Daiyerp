console.log("inside tests ui dairyb erp")
const path = require('path');
const path_join = path.resolve;
const apps_path = path_join(__dirname, '..', '..', '..', '..');
const frappe_ui_tests_path = path_join(apps_path, 'frappe', 'frappe', 'tests', 'ui');

const login = require(frappe_ui_tests_path + "/login.js")['Login'];
const welcome = require(frappe_ui_tests_path + "/setup_wizard.js")['Welcome'];
const region = require(frappe_ui_tests_path + "/setup_wizard.js")['Region'];
const user = require(frappe_ui_tests_path + "/setup_wizard.js")['User'];
const domain = require(frappe_ui_tests_path + "/setup_wizard.js")['Domain'];
const brand = require(frappe_ui_tests_path + "/setup_wizard.js")['Brand'];
const organisation = require(frappe_ui_tests_path + "/setup_wizard.js")['Organisation'];

module.exports = {
	before: browser => {
		browser
			.url(browser.launch_url + '/login')
			.waitForElementVisible('body', 5000);
	},
	'Login': login,
	'Welcome': welcome,
	'Region': region,
	'User': user,
	'Domain': domain,
	'Brand': brand,
	'Organisation': organisation,

	'Configuration': browser => {
		let slide_selector = '[data-slide-name="dairy_erp_configuration"]';
		browser
			.waitForElementVisible(slide_selector, 2000)
			.click(slide_selector + ' .next-btn');
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