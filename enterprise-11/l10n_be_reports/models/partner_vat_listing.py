# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError
from itertools import groupby


class ReportL10nBePartnerVatListing(models.AbstractModel):
    _name = "l10n.be.report.partner.vat.listing"
    _description = "Partner VAT Listing"
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    @api.model
    def get_lines(self, options, line_id=None):
        lines = []
        context = self.env.context
        if not context.get('company_ids'):
            return lines
        partner_ids = self.env['res.partner'].search([('vat', 'ilike', 'BE%')]).ids
        if not partner_ids:
            return lines

        tag_ids = [self.env['ir.model.data'].xmlid_to_res_id(k) for k in ['l10n_be.tax_tag_00', 'l10n_be.tax_tag_01', 'l10n_be.tax_tag_02', 'l10n_be.tax_tag_03', 'l10n_be.tax_tag_45', 'l10n_be.tax_tag_49']]
        tag_ids_2 = [self.env['ir.model.data'].xmlid_to_res_id(k) for k in ['l10n_be.tax_tag_54', 'l10n_be.tax_tag_64']]
        query = """
            WITH out_invoice_table AS (SELECT id FROM account_invoice WHERE type in ('out_invoice', 'out_refund') AND state in ('open', 'paid'))
            SELECT sub1.partner_id, sub1.name, sub1.vat, sub1.turnover, sub1.refund_base, sub2.vat_amount, sub2.refund_vat_amount
            FROM (SELECT l.partner_id, p.name, p.vat, SUM(l.credit - l.debit) as turnover, SUM(l.debit) as refund_base
                  FROM account_move_line l
                  LEFT JOIN res_partner p ON l.partner_id = p.id AND p.customer = true
                  RIGHT JOIN (
                      SELECT DISTINCT amlt.account_move_line_id
                      FROM account_move_line_account_tax_rel amlt
                      LEFT JOIN account_tax_account_tag tt on amlt.account_tax_id = tt.account_tax_id
                      WHERE tt.account_account_tag_id IN %(tags)s
                  ) AS x ON x.account_move_line_id = l.id
                  WHERE p.vat IS NOT NULL
                  AND l.partner_id IN %(partner_ids)s
                  AND l.date >= %(date_from)s
                  AND l.date <= %(date_to)s
                  AND l.company_id IN %(company_ids)s
                  AND ((l.invoice_id IS NULL AND l.credit > 0)
                    OR (l.invoice_id IN (SELECT id from out_invoice_table)))
                  GROUP BY l.partner_id, p.name, p.vat) AS sub1
            LEFT JOIN (SELECT l2.partner_id, SUM(l2.credit - l2.debit) as vat_amount, SUM(l2.debit) AS refund_vat_amount
                  FROM account_move_line l2
                  LEFT JOIN account_tax tax2 on l2.tax_line_id = tax2.id
                  WHERE tax2.id IN (SELECT DISTINCT(account_tax_id) from account_tax_account_tag WHERE account_account_tag_id IN %(tags2)s)
                  AND l2.partner_id IN %(partner_ids)s
                  AND l2.date >= %(date_from)s
                  AND l2.date <= %(date_to)s
                  AND l2.company_id IN %(company_ids)s
                  AND ((l2.invoice_id IS NULL AND l2.credit > 0)
                    OR (l2.invoice_id IN (SELECT id from out_invoice_table)))
                  GROUP BY l2.partner_id) AS sub2
            ON sub1.partner_id = sub2.partner_id
           WHERE turnover > 250 OR refund_base > 0 OR refund_vat_amount > 0
        """
        params = {
            'tags': tuple(tag_ids),
            'tags2': tuple(tag_ids_2),
            'partner_ids': tuple(partner_ids),
            'date_from': context['date_from'],
            'date_to': context['date_to'],
            'company_ids': tuple(context.get('company_ids')),
        }
        self.env.cr.execute(query, params)

        for record in self.env.cr.dictfetchall():
            currency_id = self.env.user.company_id.currency_id
            columns = [record['vat'].replace(' ', '').upper(), record['turnover'], record['vat_amount']]
            if not context.get('no_format', False):
                columns[1] = formatLang(self.env, columns[1] or 0.0, currency_obj=currency_id)
                columns[2] = formatLang(self.env, columns[2] or 0.0, currency_obj=currency_id)
            lines.append({
                'id': record['partner_id'],
                # 'type': 'partner_id',
                'caret_options': 'res.partner',
                'name': record['name'],
                'columns': [{'name': v } for v in columns],
                # 'level': 2,
                'unfoldable': False,
                'unfolded': False,
            })
        return lines

    def get_report_name(self):
        return _('Partner VAT Listing')

    def get_columns_name(self, options):
        return [{}, {'name': _('VAT Number')}, {'name': _('Turnover'), 'class': 'number'}, {'name': _('VAT Amount'), 'class': 'number'}]

    def get_reports_buttons(self):
        buttons = super(ReportL10nBePartnerVatListing, self).get_reports_buttons()
        buttons += [{'name': _('Export (XML)'), 'action': 'print_xml'}]
        return buttons

    def get_xml(self, options):
        # Precheck
        company = self.env.user.company_id
        company_vat = company.partner_id.vat
        if not company_vat:
            raise UserError(_('No VAT number associated with your company.'))
        default_address = company.partner_id.address_get()
        address = default_address.get('invoice', company.partner_id)
        if not address.email:
            raise UserError(_('No email address associated with the company.'))
        if not address.phone:
            raise UserError(_('No phone associated with the company.'))
        # Write xml
        seq_declarantnum = self.env['ir.sequence'].get('declarantnum')
        company_vat = company_vat.replace(' ', '').upper()
        SenderId = company_vat[2:]
        issued_by = company_vat[:2]
        dnum = company_vat[2:] + seq_declarantnum[-4:]
        street = city = country = ''
        addr = company.partner_id.address_get(['invoice'])
        if addr.get('invoice', False):
            ads = self.env['res.partner'].browse([addr['invoice']])[0]
            phone = ads.phone and ads.phone.replace(' ', '') or ''
            email = ads.email or ''
            city = ads.city or ''
            zip = ads.zip or ''
            if not city:
                city = ''
            if ads.street:
                street = ads.street
            if ads.street2:
                street += ' ' + ads.street2
            if ads.country_id:
                country = ads.country_id.code

        annual_listing_data = {
            'issued_by': issued_by,
            'company_vat': company_vat,
            'comp_name': company.name,
            'street': street,
            'zip': zip,
            'city': city,
            'country': country,
            'email': email,
            'phone': phone,
            'SenderId': SenderId,
            'period': options['date'].get('date_from')[0:4],
            'comments': self.get_report_manager(options).summary or '',
        }

        data_file = """<?xml version="1.0" encoding="ISO-8859-1"?>
  <ns2:ClientListingConsignment xmlns="http://www.minfin.fgov.be/InputCommon" xmlns:ns2="http://www.minfin.fgov.be/ClientListingConsignment" ClientListingsNbr="1">"""

        data_comp = """
        <ns2:Declarant>
            <VATNumber>%(SenderId)s</VATNumber>
            <Name>%(comp_name)s</Name>
            <Street>%(street)s</Street>
            <PostCode>%(zip)s</PostCode>
            <City>%(city)s</City>
            <CountryCode>%(country)s</CountryCode>
            <EmailAddress>%(email)s</EmailAddress>
            <Phone>%(phone)s</Phone>
        </ns2:Declarant>
        <ns2:Period>%(period)s</ns2:Period>
        """ % annual_listing_data

        # Turnover and Farmer tags are not included
        ctx = self.set_context(options)
        ctx.update({'no_format': True, 'date_from': ctx['date_from'][0:4] + '-01-01', 'date_to': ctx['date_from'][0:4] + '-12-31'})
        lines = self.with_context(ctx).get_lines(options)

        data_client_info = ''
        seq = 0
        sum_turnover = 0.00
        sum_tax = 0.00
        lines = sorted(lines, key=lambda l: l['columns'][0]['name'] or '')
        for vat, values in groupby(lines, key=lambda l: l['columns'][0]['name']):
            values = list(values)
            turnover = sum([k['columns'][1]['name'] or 0.0 for k in values])
            tax = sum([k['columns'][2]['name'] or 0.0 for k in values])
            seq += 1
            sum_turnover += turnover
            sum_tax += tax
            amount_data = {
                'seq': str(seq),
                'only_vat': vat[2:],
                'turnover': turnover,
                'vat_amount': tax,
            }
            data_client_info += """
        <ns2:Client SequenceNumber="%(seq)s">
            <ns2:CompanyVATNumber issuedBy="BE">%(only_vat)s</ns2:CompanyVATNumber>
            <ns2:TurnOver>%(turnover).2f</ns2:TurnOver>
            <ns2:VATAmount>%(vat_amount).2f</ns2:VATAmount>
        </ns2:Client>""" % amount_data

        amount_data_begin = {
            'seq': str(seq),
            'dnum': dnum,
            'sum_turnover': sum_turnover,
            'sum_tax': sum_tax,
        }
        data_begin = """
    <ns2:ClientListing SequenceNumber="1" ClientsNbr="%(seq)s" DeclarantReference="%(dnum)s"
        TurnOverSum="%(sum_turnover).2f" VATAmountSum="%(sum_tax).2f">
  """ % amount_data_begin

        data_end = """

        <ns2:Comment>%(comments)s</ns2:Comment>
    </ns2:ClientListing>
  </ns2:ClientListingConsignment>
  """ % annual_listing_data

        return data_file + data_begin + data_comp + data_client_info + data_end
