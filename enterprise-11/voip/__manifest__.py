# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "VOIP",

    'summary': """
        Make Call from all modules using the VOIP system.""",

    'description': """
        Allow to make call from next activities or with click-to-dial.
    """,

    'category': 'Sales',
    'version': '2.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'web', 'phone_validation'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mail_activity_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/voip_phonecall_views.xml',
        'views/voip_templates.xml',
        'wizard/voip_phonecall_transfer_wizard_views.xml',
        'data/mail_activity_data.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'application': True,
    'license': 'OEEL-1',
}
