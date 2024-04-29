# -*- coding: utf-8 -*-

from odoo import models
from odoo.osv import expression


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _get_compute_timesheet_revenue_domain(self, so_line_ids):
        domain = super(AccountInvoice, self)._get_compute_timesheet_revenue_domain(so_line_ids)
        if self.env['res.config.settings'].invoiced_timesheet == 'approved':
            domain = expression.AND([domain, [('validated', '=', True)]])
        return domain
