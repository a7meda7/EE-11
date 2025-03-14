# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo.tests.common import TransactionCase
from odoo.modules.module import get_module_resource


class TestQifFile(TransactionCase):
    """Tests for import bank statement qif file format (account.bank.statement.import)
    """

    def setUp(self):
        super(TestQifFile, self).setUp()
        self.BankStatementImport = self.env['account.bank.statement.import']
        self.BankStatement = self.env['account.bank.statement']
        self.BankStatementLine = self.env['account.bank.statement.line']

    def test_qif_file_import(self):
        from odoo.tools import float_compare
        qif_file_path = get_module_resource('account_bank_statement_import_qif', 'test_qif_file', 'test_qif.qif')
        qif_file = base64.b64encode(open(qif_file_path, 'rb').read())
        bank_statement_id = self.BankStatementImport.create(dict(data_file=qif_file,))
        journal = self.env['account.journal'].create({'type': 'bank', 'name': 'bank QIF', 'code': 'BNK67'})
        bank_statement_id.with_context(journal_id=journal.id).import_file()
        line = self.BankStatementLine.search([('name', '=', 'YOUR LOCAL SUPERMARKET')], limit=1)
        assert float_compare(line.statement_id.balance_end_real, -1896.09, 2) == 0
