# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import api, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError


class ReportL10nBePartnerVatIntra(models.AbstractModel):
    _name = "l10n.be.report.partner.vat.intra"
    _description = "Partner VAT Intra"
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    @api.model
    def get_lines(self, options, line_id=None):
        lines = []
        context = self.env.context
        if not context.get('company_ids'):
            return lines
        seq = amount_sum = 0
        tag_ids = [self.env['ir.model.data'].xmlid_to_res_id(k) for k in ['l10n_be.tax_tag_44', 'l10n_be.tax_tag_46L', 'l10n_be.tax_tag_46T']]
        query = """
            SELECT p.name As partner_name, l.partner_id AS partner_id, p.vat AS vat,
                      tt.account_account_tag_id AS intra_code, SUM(-l.balance) AS amount
                      FROM account_move_line l
                      LEFT JOIN res_partner p ON l.partner_id = p.id
                      LEFT JOIN account_move_line_account_tax_rel amlt ON l.id = amlt.account_move_line_id
                      LEFT JOIN account_tax_account_tag tt on amlt.account_tax_id = tt.account_tax_id
                      WHERE tt.account_account_tag_id IN %s
                       AND l.date >= %s
                       AND l.date <= %s
                       AND l.company_id IN %s
                      GROUP BY p.name, l.partner_id, p.vat, intra_code
        """
        params = (tuple(tag_ids), context.get('date_from'),
                  context.get('date_to'), tuple(context.get('company_ids')))
        self.env.cr.execute(query, params)
        p_count = 0

        for row in self.env.cr.dictfetchall():
            if not row['vat']:
                row['vat'] = ''
                p_count += 1

            amt = row['amount'] or 0.0
            if amt:
                seq += 1
                amount_sum += amt

                [intra_code, code] = row['intra_code'] == tag_ids[0] and ['44', 'S'] or (row['intra_code'] == tag_ids[1] and ['46L', 'L'] or (row['intra_code'] == tag_ids[2] and ['46T', 'T'] or ['', '']))

                columns = [row['vat'].replace(' ', '').upper(), code, intra_code, amt]
                if not context.get('no_format', False):
                    currency_id = self.env.user.company_id.currency_id
                    columns[3] = formatLang(self.env, columns[3], currency_obj=currency_id)

                lines.append({
                    'id': row['partner_id'],
                    # 'type': 'partner_id',
                    'caret_options': 'res.partner',
                    'name': row['partner_name'],
                    'columns': [{'name': v } for v in columns],
                    # 'level': 2,
                    'unfoldable': False,
                    'unfolded': False,
                })

        if context.get('get_xml_data'):
            return {'lines': lines, 'clientnbr': str(seq), 'amountsum': round(amount_sum, 2), 'partner_wo_vat': p_count}
        return lines

    def get_report_name(self):
        return _('Partner VAT Intra')

    def get_columns_name(self, options):
        return [{}, {'name': _('VAT Number')}, {'name': _('Code')}, {'name': _('Intra Code')}, {'name': _('Amount'), 'class': 'number'}]

    def get_reports_buttons(self):
        buttons = super(ReportL10nBePartnerVatIntra, self).get_reports_buttons()
        buttons += [{'name': _('Export (XML)'), 'action': 'print_xml'}]
        return buttons

    def get_xml(self, options):
        # Check
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

        # Generate xml
        post_code = street = city = country = data_clientinfo = ''
        company_vat = company_vat.replace(' ', '').upper()
        issued_by = company_vat[:2]

        seq_declarantnum = self.env['ir.sequence'].get('declarantnum')
        dnum = company_vat[2:] + seq_declarantnum[-4:]

        addr = company.partner_id.address_get(['invoice'])
        if addr.get('invoice', False):
            ads = self.env['res.partner'].browse([addr['invoice']])[0]
            phone = ads.phone and ads.phone.replace(' ', '') or ''
            email = ads.email or ''
            city = ads.city or ''
            post_code = ads.zip or ''
            if not city:
                city = ''
            if ads.street:
                street = ads.street
            if ads.street2:
                street += ' ' + ads.street2
            if ads.country_id:
                country = ads.country_id.code

        if not country:
            country = company_vat[:2]

        date_from = options['date'].get('date_from')
        date_to = options['date'].get('date_to')

        ctx = self.set_context(options)
        ctx.update({'no_format': True, 'date_from': date_from, 'date_to': date_to, 'get_xml_data': True})
        xml_data = self.with_context(ctx).get_lines(options)

        ctx_date_from = date_from[5:10]
        ctx_date_to = date_to[5:10]
        month = None
        quarter = None
        if ctx_date_from == '01-01' and ctx_date_to == '03-31':
            quarter = '1'
        elif ctx_date_from == '04-01' and ctx_date_to == '06-30':
            quarter = '2'
        elif ctx_date_from == '07-01' and ctx_date_to == '09-30':
            quarter = '3'
        elif ctx_date_from == '10-01' and ctx_date_to == '12-31':
            quarter = '4'
        elif ctx_date_from != '01-01' or ctx_date_to != '12-31':
            month = date_from[5:7]

        xml_data.update({
            'company_name': company.name,
            'company_vat': company_vat,
            'vatnum': company_vat[2:],
            'sender_date': str(time.strftime('%Y-%m-%d')),
            'street': street,
            'city': city,
            'post_code': post_code,
            'country': country,
            'email': email,
            'phone': phone.replace('/', '').replace('.', '').replace('(', '').replace(')', '').replace(' ', ''),
            'year': date_from[0:4],
            'month': month,
            'quarter': quarter,
            'comments': self.get_report_manager(options).summary or '',
            'issued_by': issued_by,
            'dnum': dnum,
        })

        data_head = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ns2:IntraConsignment xmlns="http://www.minfin.fgov.be/InputCommon" xmlns:ns2="http://www.minfin.fgov.be/IntraConsignment" IntraListingsNbr="1">"""
        data_comp_period = '\n\t\t<ns2:Declarant>\n\t\t\t<VATNumber>%(vatnum)s</VATNumber>\n\t\t\t<Name>%(company_name)s</Name>\n\t\t\t<Street>%(street)s</Street>\n\t\t\t<PostCode>%(post_code)s</PostCode>\n\t\t\t<City>%(city)s</City>\n\t\t\t<CountryCode>%(country)s</CountryCode>\n\t\t\t<EmailAddress>%(email)s</EmailAddress>\n\t\t\t<Phone>%(phone)s</Phone>\n\t\t</ns2:Declarant>'
        data_comp_period += '\n\t\t<ns2:Period>\n'
        if month:
            data_comp_period += '\t\t\t<ns2:Month>%(month)s</ns2:Month>\n'
        elif quarter:
            data_comp_period += '\t\t\t<ns2:Quarter>%(quarter)s</ns2:Quarter>\n'
        data_comp_period += '\t\t\t<ns2:Year>%(year)s</ns2:Year>\n\t\t</ns2:Period>'
        data_comp_period %= xml_data

        data_clientinfo = ''
        seq = 0
        for line in xml_data['lines']:
            seq += 1
            vat = line['columns'][0].get('name', False)
            if not vat:
                raise UserError(_('No vat number defined for %s.') % line['name'])
            client = {
                'partner_name': line['name'],
                'vatnum': vat[2:].replace(' ', '').upper(),
                'vat': vat,
                'country': vat[:2],
                'amount': line['columns'][3].get('name', 0.0),
                'intra_code': line['columns'][2].get('name', ''),
                'code': line['columns'][1].get('name', ''),
                'seq': seq,
            }
            data_clientinfo += '\n\t\t<ns2:IntraClient SequenceNumber="%(seq)s">\n\t\t\t<ns2:CompanyVATNumber issuedBy="%(country)s">%(vatnum)s</ns2:CompanyVATNumber>\n\t\t\t<ns2:Code>%(code)s</ns2:Code>\n\t\t\t<ns2:Amount>%(amount).2f</ns2:Amount>\n\t\t</ns2:IntraClient>' % (client)

        data_decl = '\n\t<ns2:IntraListing SequenceNumber="1" ClientsNbr="%(clientnbr)s" DeclarantReference="%(dnum)s" AmountSum="%(amountsum).2f">' % (xml_data)

        return data_head + data_decl + data_comp_period + data_clientinfo + '\n\t\t</ns2:IntraListing>\n</ns2:IntraConsignment>' % (xml_data)
