odoo.define('account_reports.tour', function (require) {
'use strict';

var Tour = require('web_tour.tour');

Tour.register('account_followup_reports_widgets', {
    test: true,
    url: '/web?#action=account_reports.action_account_followup_all',
    },
     [
        {
            content: 'wait for web client',
            trigger: "#trustDropdown",
            extra_trigger: ".breadcrumb",
            run: function() {}
        },
        {
            content: 'click trust ball',
            trigger: '#trustDropdown',
            run: 'click'
        },
        {
            content: 'change trust',
            trigger: '.changeTrust[data-new-trust="good"]',
            run: 'click'
        },
        {
            content: 'exclude one line',
            trigger: '.o_account_reports_table tr:not(:has(td.color-red)) input[type="checkbox"]:first',
            run: 'click'
        },
        {
            content: 'ensure that line has been excluded',
            trigger: '.o_account_reports_table .o_account_followup_blocked',
            run: function() {}
        },
        {
            content: 'send by mail',
            trigger: '.followup-email',
            run: 'click'
        },
        {
            content: 'check that message telling that mail has been sent is shown',
            trigger: '.alert:contains(The followup report was successfully emailed !)',
            run: function() {}
        },
        {
            content: 'dismiss alert',
            trigger: '.alert .close',
            run: 'click'
        },
        {
            content:      "change filter",
            trigger:    ".o_account_reports_followup-filter > a",
        },
        {
            content:      "change filter",
            trigger:    ".js_account_reports_one_choice_filter[data-id='all'] > a",
            run: 'click'
        },
        {
            content: "open history button",
            trigger: '#history:visible .dropdown > a',
            run: 'click'
        },
        // TODO /!\ fix this fragile selector, since other modules can insert other overdue invoices for Agrolait
        //          and then block the tour
        {
            content: "Check that sent mail has only 2 invoices",
            trigger: '.o_account_reports_history li table:first tbody:not(:has(tr:has(td:contains(INV))+tr:has(td:contains(INV))+tr:has(td:contains(INV))+tr:has(td:contains(Total))))',
            extra_trigger: '.o_account_reports_history li table:first tbody:has(tr:has(td:contains(INV))+tr:has(td:contains(INV))+tr:has(td:contains(Total)))',
            run: function() {}
        },
        {
            content:      "change filter",
            trigger:    ".o_account_reports_followup-filter > a",
        },
        {
            content:      "change filter",
            trigger:    ".js_account_reports_one_choice_filter[data-id='action'] > a",
            run: 'click'
        },
        {
            content: 'Click the Do it later button',
            trigger: '.o_account_reports_followup_skip',
            run: 'click'
        },
        {
            content: 'Check that we have nothing to display',
            trigger: '.alert-info:contains(No followup to send ! You have skipped 1 partners)'
        },

     ]
);

});
