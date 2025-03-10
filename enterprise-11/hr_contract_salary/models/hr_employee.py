# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    additional_note = fields.Text(string='Additional Note', groups="hr.group_hr_user")
    certificate = fields.Selection([
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('other', 'Other'),
    ], 'Certificate Level', default='master', groups="hr.group_hr_user")
    study_field = fields.Char("Field of Study", placeholder='Computer Science', groups="hr.group_hr_user")
    study_school = fields.Char("School", groups="hr.group_hr_user")
    emergency_contact = fields.Char("Emergency Contact", groups="hr.group_hr_user")
    emergency_phone = fields.Char("Emergency Phone", groups="hr.group_hr_user")

    def open_package_employee(self):
        self.ensure_one()
        return self.contract_id.open_package_contract()

    def get_partner_values(self, personal_info):
        return {
            'street': personal_info['street'],
            'street2': personal_info['street2'],
            'city': personal_info['city'],
            'zip': personal_info['zip'],
            'state_id': self.env['res.country.state'].search([('name', '=', personal_info['state'])], limit=1).id,
            'country_id': personal_info['country'],
            'phone': personal_info['phone'],
            'email': personal_info['email'],
            'type': 'other',
        }

    def get_employee_values(self, personal_info):
        return {
            'gender': personal_info['gender'],
            'disabled': personal_info['disabled'],
            'marital': personal_info['marital'],
            'spouse_fiscal_status': personal_info['spouse_fiscal_status'],
            'spouse_net_revenue': personal_info['spouse_net_revenue'],
            'spouse_other_net_revenue': personal_info['spouse_other_net_revenue'],
            'disabled_spouse_bool': personal_info['disabled_spouse_bool'],
            'children': personal_info['children_count'],
            'disabled_children_bool': personal_info['disabled_children'],
            'disabled_children_number': personal_info['disabled_children_count'],
            'other_dependent_people': personal_info['other_dependent_people'],
            'other_senior_dependent': personal_info['other_senior_dependent'],
            'other_disabled_senior_dependent': personal_info['other_disabled_senior_dependent'],
            'other_juniors_dependent': personal_info['other_juniors_dependent'],
            'other_disabled_juniors_dependent': personal_info['other_disabled_juniors_dependent'],
            'identification_id': personal_info['national_number'],
            'country_id': personal_info['nationality'],
            'emergency_contact': personal_info['emergency_person'],
            'emergency_phone': personal_info['emergency_phone_number'],
            'certificate': personal_info['certificate'],
            'study_field': personal_info['certificate_name'],
            'study_school': personal_info['certificate_school'],
        }

    def update_personal_info(self, personal_info, no_name_write=False):
        self.ensure_one()

        # Update personal info on the partner
        partner_values = self.get_partner_values(personal_info)

        if self.address_home_id:
            partner = self.address_home_id
            # We shouldn't modify the partner email like this
            partner_values.pop('email', None)
            self.address_home_id.write(partner_values)
        else:
            partner = self.env['res.partner'].create(partner_values)

        # Update personal info on the employee
        vals = self.get_employee_values(personal_info)

        existing_bank_account = self.env['res.partner.bank'].search([('acc_number', '=', personal_info['bank_account'])])
        if existing_bank_account:
            bank_account = existing_bank_account
        else:
            bank_account = self.env['res.partner.bank'].create({
                'acc_number': personal_info['bank_account'],
                'partner_id': partner.id,
            })
        vals['bank_account_id'] = bank_account.id
        vals['address_home_id'] = partner.id

        if not no_name_write:
            vals['name'] = personal_info['name']

        if personal_info['birthdate'] != '':
            vals.update({'birthday': personal_info['birthdate']})
        self.write(vals)
