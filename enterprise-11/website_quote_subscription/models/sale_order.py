# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _name = "sale.order"

    def _get_payment_type(self):
        if any(line.product_id.recurring_invoice for line in self.sudo().order_line):
            return 'form_save'
        return super(SaleOrder, self)._get_payment_type()

    def _get_subscription_lines(self):
        """ Extract lines related to subscriptions. """
        self.ensure_one()
        res = dict()
        for line in self.order_line.filtered('recurring_product'):
            res.setdefault(line.product_id.subscription_template_id, self.env['sale.order.line'])
            res[line.product_id.subscription_template_id] |= line
        return res

class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = "sale.order.line"

    recurring_product = fields.Boolean('Recurring Product', related="product_id.recurring_invoice")
