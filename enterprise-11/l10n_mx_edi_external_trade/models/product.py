# coding: utf-8

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_mx_edi_tariff_fraction_id = fields.Many2one(
        'l10n_mx_edi.tariff.fraction', string='Tariff Fraction',
        help='It is used to express the key of the tariff fraction '
        'corresponding to the description of the product exported. Node '
        '"FraccionArancelaria" to concept.')
    l10n_mx_edi_umt_aduana_id = fields.Many2one(
        'product.uom', 'UMT Aduana', help='Used in complement '
        '"Comercio Exterior" to indicate in the products the '
        'TIGIE Units of Measurement, this based in the SAT catalog.')


class ProductUoM(models.Model):
    _inherit = 'product.uom'

    l10n_mx_edi_code_aduana = fields.Char(
        'Code Aduana', help='Used in the complement of "Comercio Exterior" to '
        'indicate in the products the UoM, this based in the SAT catalog.')


class L10nMXEdiTariffFraction(models.Model):
    _name = 'l10n_mx_edi.tariff.fraction'

    code = fields.Char(help='Code defined in the SAT to this record.')
    name = fields.Char(help='Name defined in the SAT catalog to this record.')
    uom_code = fields.Char(
        help='UoM code related with this tariff fraction, this value is '
        'defined in the SAT catalog and will be assigned in the attribute '
        '"UnidadAduana" in the merchandise.')
    active = fields.Boolean(
        help='If the tariff fraction has expired could be disabled todo not '
        'allow select the record.', default=True)

    @api.multi
    def name_get(self):
        result = []
        for tariff in self:
            result.append((tariff.id, "%s %s" % (
                tariff.code, tariff.name or '')))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain_name = ['|', ('name', 'ilike', name), ('code', 'ilike', name)]
        recs = self.search(domain_name + args, limit=limit)
        return recs.name_get()
