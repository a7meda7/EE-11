# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
  'name': "eBay Connector",

  'summary': """
  Publish your products on eBay""",

  'description': """
Publish your products on eBay
=============================

The eBay integrator gives you the opportunity to manage your Odoo's products on eBay.

Key Features
------------
* Publish products on eBay
* Revise, relist, end items on eBay
* Integration with the stock moves
* Automatic creation of sales order and invoices

  """,

  # Categories can be used to filter modules in modules listing
  # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
  # for the full list
  'category': 'Sales',
  'version': '1.0',

  # any module necessary for this one to work correctly
  'depends': ['base', 'sale_management', 'stock', 'delivery', 'document'],
  'external_dependencies': {'python': ['ebaysdk']},

  # always loaded
  'data': [
      'security/ir.model.access.csv',
      'security/sale_ebay_security.xml',
      'wizard/ebay_link_listing_views.xml',
      'views/product_views.xml',
      'views/res_config_settings_views.xml',
      'views/res_partner_views.xml',
      'views/stock_picking_views.xml',
      'data/mail_template_data.xml',
      'data/ir_cron_data.xml',
      'data/sale_ebay_data.xml',
      'data/product_data.xml',
  ],
  # only loaded in demonstration mode
  'demo': [
  ],
  'js': ['static/src/js/*.js'],
  'css': ['static/src/css/*.css'],
  'qweb': ['static/src/xml/*.xml'],
  'application': False,
    'license': 'OEEL-1',
  'uninstall_hook': 'uninstall_hook',
}
