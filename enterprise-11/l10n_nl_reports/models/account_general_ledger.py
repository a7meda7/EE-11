# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, release, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.xml_utils import _check_with_xsd

import calendar
import json

from dateutil.rrule import rrule, MONTHLY
from datetime import datetime
from collections import namedtuple
from itertools import groupby


class ReportAccountGeneralLedger(models.AbstractModel):
    _inherit = 'account.general.ledger'

    def get_reports_buttons(self):
        buttons = super(ReportAccountGeneralLedger, self).get_reports_buttons()
        buttons.append({'name': _('EXPORT (XAF)'), 'action': 'l10n_nl_print_xaf'})
        return buttons

    def get_xaf(self, options):
        def cust_sup_tp(partner_id):
            if partner_id.customer and partner_id.supplier:
                return 'B'
            if partner_id.customer:
                return 'C'
            if partner_id.supplier:
                return 'S'
            return 'O'

        def acc_tp(account_id):
            if account_id.user_type_id.type in ['income', 'expense']:
                return 'P'
            if account_id.user_type_id.type in ['asset', 'liability']:
                return 'B'
            return 'M'

        def jrn_tp(journal_id):
            if journal_id.type == 'bank':
                return 'B'
            if journal_id.type == 'cash':
                return 'C'
            if journal_id.type == 'situation':
                return 'O'
            if journal_id.type in ['sale', 'sale_refund']:
                return 'S'
            if journal_id.type in ['purchase', 'purchase_refund']:
                return 'P'
            return 'Z'

        def amnt_tp(move_line_id):
            return 'C' if move_line_id.credit else 'D'

        def compute_period_number(date_str):
            date = datetime.strptime(date_str, DEFAULT_SERVER_DATE_FORMAT)
            return date.strftime('%y%m')[1:]

        def change_date_time(record):
            date = datetime.strptime(record.write_date, DEFAULT_SERVER_DATETIME_FORMAT)
            return date.strftime('%Y-%m-%dT%H:%M:%S')

        company_id = self.env.user.company_id

        msgs = []

        if not company_id.vat:
            msgs.append(_('- VAT number'))
        if not company_id.country_id:
            msgs.append(_('- Country'))

        if msgs:
            msgs = [_('Some fields must be specified on the company:')] + msgs
            raise UserError('\n'.join(msgs))

        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        partner_ids = self.env['res.partner'].search(
            ['|', ('customer', '=', True), ('supplier', '=', True),
             '|', ('company_id', '=', False), ('company_id', '=', company_id.id)])
        account_ids = self.env['account.account'].search([('company_id', '=', company_id.id)])
        tax_ids = self.env['account.tax'].search([('company_id', '=', company_id.id)])
        journal_ids = self.env['account.journal'].search([('company_id', '=', company_id.id)])
        # Retrieve periods values
        periods = []
        Period = namedtuple('Period', 'number name date_from date_to')
        for period in rrule(freq=MONTHLY, bymonth=(), dtstart=fields.Date.from_string(date_from), until=fields.Date.from_string(date_to)):
            period_from = fields.Date.to_string(period.date())
            period_to = period.replace(day=calendar.monthrange(period.year, period.month)[1])
            period_to = fields.Date.to_string(period_to.date())
            periods.append(Period(
                number=compute_period_number(period_from),
                name=period.strftime('%B') + ' ' + date_from[0:4],
                date_from=period_from,
                date_to=period_to
            ))
        # Retrieve move lines values
        total_query = """
            SELECT COUNT(*), SUM(l.debit), SUM(l.credit)
            FROM account_move_line l, account_move m
            WHERE l.move_id = m.id
            AND l.date >= %s
            AND l.date <= %s
            AND l.company_id = %s
            AND m.state != 'draft'
        """
        self.env.cr.execute(total_query, (date_from, date_to, company_id.id,))
        moves_count, moves_debit, moves_credit = self.env.cr.fetchall()[0]
        journal_x_moves = {}
        for journal in journal_ids:
            journal_x_moves[journal] = self.env['account.move'].search(
                [('date', '>=', date_from), ('date', '<=', date_to), ('state', '!=', 'draft'), ('journal_id', '=', journal.id)])
        values = {
            'company_id': company_id,
            'partner_ids': partner_ids,
            'account_ids': account_ids,
            'journal_ids': journal_ids,
            'journal_x_moves': journal_x_moves,
            'compute_period_number': compute_period_number,
            'periods': periods,
            'tax_ids': tax_ids,
            'cust_sup_tp': cust_sup_tp,
            'acc_tp': acc_tp,
            'jrn_tp': jrn_tp,
            'amnt_tp': amnt_tp,
            'change_date_time': change_date_time,
            'fiscal_year': date_from[0:4],
            'date_from': date_from,
            'date_to': date_to,
            'date_created': fields.Datetime.now()[:10],
            'software_version': release.version,
            'moves_count': moves_count,
            'moves_debit': moves_debit,
            'moves_credit': moves_credit,
        }
        audit_content = self.env['ir.qweb'].render('l10n_nl_reports.xaf_audit_file', values)
        with tools.file_open('l10n_nl_reports/data/xml_audit_file_3_2.xsd', 'rb') as xsd:
            _check_with_xsd(audit_content, xsd)
        return audit_content

    def l10n_nl_print_xaf(self, options):
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': self.env.context.get('model'),
                         'options': json.dumps(options),
                         'output_format': 'xaf',
                         'financial_id': self.env.context.get('id'),
                         }
                }
