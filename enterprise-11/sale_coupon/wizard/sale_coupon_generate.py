# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleCouponGenerate(models.TransientModel):
    _name = 'sale.coupon.generate'

    nbr_coupons = fields.Integer(string="Number of Coupons", help="Number of coupons", default=1)
    generation_type = fields.Selection([
        ('nbr_coupon', 'Number of Coupons'),
        ('nbr_customer', 'Number of Selected Customers')
        ], default='nbr_coupon')
    partners_domain = fields.Char(string="Customer", default='[]')

    @api.multi
    def generate_coupon(self):
        """Generates the number of coupons entered in wizard field nbr_coupons
        """
        program = self.env['sale.coupon.program'].browse(self.env.context.get('active_id'))

        vals = {'program_id': program.id}

        if self.generation_type == 'nbr_coupon' and self.nbr_coupons > 0:
            for count in range(0, self.nbr_coupons):
                self.env['sale.coupon'].create(vals)

        if self.generation_type == 'nbr_customer' and self.partners_domain:
            for partner in self.env['res.partner'].search(safe_eval(self.partners_domain)):
                vals.update({'partner_id': partner.id})
                coupon = self.env['sale.coupon'].create(vals)
                subject = '%s, a coupon has been generated for you' % (partner.name)
                body = self.env.ref('sale_coupon.sale_coupon_created_coupon_email_template').render({
                    'code': coupon.code,
                    'reward_description': coupon.program_id.discount_line_product_id.name
                    })
                self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.env.user.email or '',
                    'email_to': partner.email,
                })
