import unittest
from odoo.tests.common import TransactionCase


@unittest.skip("Currency rate live test disabled as it requires to contact external servers")
class CurrencyTestCase(TransactionCase):

    def setUp(self):
        super(CurrencyTestCase, self).setUp()
        self.test_company = self.env['res.company'].create({'name': 'Test Company'})
        # Each test will check the number of rates for USD
        self.currency_usd = self.env.ref('base.USD')

    def test_live_currency_update_ecb(self):
        self.test_company.currency_provider = 'ecb'
        rates_count = len(self.currency_usd.rate_ids)
        res = self.test_company._update_currency_ecb()
        self.assertTrue(res)
        self.assertEqual(len(self.currency_usd.rate_ids), rates_count + 1)


    def test_live_currency_update_fta(self):
        self.test_company.currency_provider = 'fta'
        # testing Swiss Federal Tax Administration requires that Franc Suisse can be found
        # which is not the case in runbot/demo data as l10n_ch is not always installed
        self.env.ref('base.CHF').write({'active': True})
        rates_count = len(self.currency_usd.rate_ids)
        res = self.test_company._update_currency_fta()
        self.assertTrue(res)
        self.assertEqual(len(self.currency_usd.rate_ids), rates_count + 1)

    def test_live_currency_update_banxico(self):
        self.test_company.currency_provider = 'banxico'
        rates_count = len(self.currency_usd.rate_ids)
        res = self.test_company._update_currency_banxico()
        self.assertTrue(res)
        self.assertEqual(len(self.currency_usd.rate_ids), rates_count + 1)