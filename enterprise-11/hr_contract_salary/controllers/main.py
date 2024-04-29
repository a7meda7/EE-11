# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo import http

from odoo.addons.website_sign.controllers.main import WebsiteSign
from odoo.http import request
from odoo.exceptions import AccessError

class website_hr_contract_salary(http.Controller):

    def _check_token_validity(self, token):
        if token:
            contract = request.env['hr.contract'].sudo().search([
                ('access_token', '=', token),
                ('access_token_end_date', '>=', fields.Date.today()),
                ('access_token_consumed', '=', False),
            ], limit=1)
            return contract
        return request.env['hr.contract']

    def _check_employee_access_right(self, contract_id):
        contract_sudo = request.env['hr.contract'].sudo().browse(contract_id)
        if not contract_sudo.employee_id or contract_sudo.employee_id.user_id == request.env.user:
            return contract_sudo
        try:
            contract = request.env['hr.contract'].browse(contract_id)
            contract.check_access_rights('read')
            contract.check_access_rule('read')
        except AccessError:
            return request.env['hr.contract']
        return contract

    @http.route(['/salary_package/contract/<int:contract_id>'], type='http', auth="user", website=True)
    def salary_package(self, contract_id=None, **kw):
        contract = self._check_employee_access_right(contract_id)
        if not contract:
            return request.not_found()
        values = self.get_salary_package_values(contract)
        values.update({'need_personal_information': False, 'submit': True})
        return request.render("hr_contract_salary.salary_package", values)

    @http.route(['/salary_package/contract/<string:token>'], type='http', auth='public', website=True)
    def salary_package_applicant(self, token=None, **kw):
        contract = self._check_token_validity(token)
        if not contract:
            return request.not_found()
        values = self.get_salary_package_values(contract)
        values.update({
            'need_personal_information': True,
            'token': token,
            'submit': True
        })
        return request.render("hr_contract_salary.salary_package", values)

    @http.route(['/salary_package/job/<int:job_id>'], type='http', auth="user", website=True)
    def salary_package_job_position(self, job_id=None, **kw):
        try:
            job = request.env['hr.job'].browse(job_id)
            job.check_access_rights('read')
            job.check_access_rule('read')
        except AccessError:
            return request.not_found()

        contract = job.default_contract_id

        if not contract:
            return request.render('website.404')
        values = self.get_salary_package_values(contract)
        values.update({'need_personal_information': False, 'submit': False})
        return request.render("hr_contract_salary.salary_package", values)

    @http.route(['/salary_package/thank_you/<int:job_id>'], type='http', auth="public", website=True)
    def salary_package_thank_you(self, job_id=None, **kw):
        job = request.env['hr.job'].sudo().browse(job_id)
        return request.render("hr_contract_salary.salary_package_thank_you", {
            'responsible_name': job.hr_responsible_id.partner_id.name or job.user_id.partner_id.name,
            'responsible_email': job.hr_responsible_id.partner_id.email or job.user_id.partner_id.email,
            'responsible_phone': job.hr_responsible_id.partner_id.phone or job.user_id.partner_id.phone,
        })

    def get_salary_package_values(self, contract):
        return {
            'contract': contract,
            'available_cars': request.env['fleet.vehicle'].sudo().search(
                contract._get_available_cars_domain()).sorted(key=lambda car: car.total_depreciated_cost),
            'can_be_requested_models': request.env['fleet.vehicle.model'].sudo().search(
                contract._get_possible_model_domain()).sorted(key=lambda model: model.default_total_depreciated_cost),
            'states': request.env['res.country.state'].search([]),
            'countries': request.env['res.country'].search([]),
        }

    def create_new_contract(self, contract, advantages, no_write=False, **kw):
        # Generate a new contract with the current modifications
        personal_info = advantages['personal_info']

        if kw.get('employee'):
            employee = kw.get('employee')
        elif contract.employee_id:
            employee = contract.employee_id
        else:
            employee = request.env['hr.employee'].sudo().create({
                'name': 'Simulation Employee',
            })
        if personal_info:
            employee.update_personal_info(personal_info, no_name_write=bool(kw.get('employee')))
        new_contract = request.env['hr.contract'].sudo().new({
            'name': contract.name if contract.state == 'draft' else "Package Simulation",
            'job_id': contract.job_id.id,
            'company_id': contract.company_id.id,
            'currency_id': contract.company_id.currency_id.id,
            'employee_id': employee.id,
            'struct_id': contract.struct_id.id,
            'company_car_total_depreciated_cost': contract.company_car_total_depreciated_cost,
            'wage': advantages['wage'],
            'resource_calendar_id': contract.resource_calendar_id.id,
            'transport_mode': advantages['transport_mode'],
            'public_transport_employee_amount': advantages['public_transport_employee_amount'],
            'others_reimbursed_amount': advantages['others_reimbursed_amount'],
            'eco_checks': advantages['eco_checks'],
            'fuel_card': advantages['fuel_card'],
            'holidays': advantages['holidays'],
            'commission_on_target': advantages['commission_on_target'],
            'representation_fees': advantages['representation_fees'],
            'meal_voucher_amount': advantages['meal_voucher_amount'] / 20.0,
            'signature_request_template_id': contract.signature_request_template_id.id,
        })
        new_contract.set_attribute_value('internet', advantages['has_internet'])
        new_contract.set_attribute_value('mobile', advantages['has_mobile'])
        new_contract.set_attribute_value('mobile_plus', advantages['international_communication'])
        if advantages['transport_mode'] == 'company_car':
            if advantages['new_car']:
                new_contract.new_car = True
                new_contract.new_car_model_id = advantages['car_id']
            else:
                new_contract.new_car = False
                new_contract.car_id = advantages['car_id']
        else:
            new_contract.new_car = False
            new_contract.new_car_model_id = False
            new_contract.car_id = False

        if advantages['transport_mode'] != 'public_transport':
            new_contract.public_transport_employee_amount = False
        if advantages['transport_mode'] != 'others':
            new_contract.others_reimbursed_amount = False

        new_contract.wage_with_holidays = advantages['wage']
        new_contract.final_yearly_costs = advantages['final_yearly_costs']
        new_contract._inverse_wage_with_holidays()

        vals = new_contract._convert_to_write(new_contract._cache)
        if not no_write and contract.state == 'draft':
            contract.write(vals)
            return contract
        else:
            return request.env['hr.contract'].sudo().create(vals)

    @http.route(['/salary_package/update_gross/'], type="json", auth="public")
    def update_gross(self, contract_id=None, token=None, advantages=None, **kw):

        result = {}

        if token:
            contract = self._check_token_validity(token)
        else:
            contract = self._check_employee_access_right(contract_id)

        new_contract = self.create_new_contract(contract, advantages)
        new_gross = new_contract._get_gross_from_employer_costs(advantages['final_yearly_costs'])
        new_contract.wage = new_gross

        result.update({'new_gross': round(new_gross, 2)})

        request.env.cr.rollback()

        return result

    @http.route(['/salary_package/compute_net/'], type='json', auth='public')
    def compute_net(self, contract_id=None, token=None, advantages=None, **kw):

        if token:
            contract = self._check_token_validity(token)
        else:
            contract = self._check_employee_access_right(contract_id)

        new_contract = self.create_new_contract(contract, advantages)
        #  Update gross to keep a fixed employer cost
        new_gross = new_contract._get_gross_from_employer_costs(advantages['final_yearly_costs'])
        new_contract.wage = new_gross

        # generate a payslip corresponding to only this contract
        payslip = request.env['hr.payslip'].sudo().create({
            'employee_id': new_contract.employee_id.id,
            'contract_id': new_contract.id,
            'struct_id': new_contract.struct_id.id,
            'company_id': new_contract.employee_id.company_id.id,
            'name': 'Payslip Simulation',
            'date_from': request.env['hr.payslip'].default_get(['date_from'])['date_from'],
            'date_to': request.env['hr.payslip'].default_get(['date_to'])['date_to'],
        })

        for worked_days_line_vals in payslip.get_worked_day_lines(new_contract, payslip.date_from, payslip.date_to):
            payslip.worked_days_line_ids += request.env['hr.payslip.worked_days'].sudo().new(worked_days_line_vals)
        for inputs_line_vals in payslip.get_inputs(new_contract, payslip.date_from, payslip.date_to):
            payslip.input_line_ids += request.env['hr.payslip.input'].sudo().new(inputs_line_vals)

        payslip.compute_sheet()

        result = self.get_compute_results(new_contract, payslip)

        request.env.cr.rollback()

        return result

    def get_compute_results(self, new_contract, payslip):
        result = {}
        result.update({
            'BASIC': round(payslip.get_salary_line_total('BASIC'), 2),
            'SALARY': round(payslip.get_salary_line_total('SALARY'), 2),
            'ONSS': round(payslip.get_salary_line_total('ONSS'), 2),
            'EMP.BONUS': round(payslip.get_salary_line_total('EmpBonus.1'), 2) or round(payslip.get_salary_line_total('EmpBonus.2'), 2),
            'GROSS': round(payslip.get_salary_line_total('GROSS'), 2),
            'REP.FEES': round(payslip.get_salary_line_total('REP.FEES'), 2),
            'P.P': round(payslip.get_salary_line_total('P.P'), 2),
            'PP.RED': round(
                payslip.get_salary_line_total('Ch.A') +
                payslip.get_salary_line_total('Red.Iso') +
                payslip.get_salary_line_total('Red.Iso.Par') +
                payslip.get_salary_line_total('Red.Dis') +
                payslip.get_salary_line_total('Red.Seniors') +
                payslip.get_salary_line_total('Red.Juniors') +
                payslip.get_salary_line_total('Sp.handicap') +
                payslip.get_salary_line_total('Red.Spouse.Net') +
                payslip.get_salary_line_total('Red.Spouse.Oth.Net'), 2),
            'M.ONSS': round(payslip.get_salary_line_total('M.ONSS.1'), 2) or round(payslip.get_salary_line_total('M.ONSS.2'), 2),
            'MEAL_V_EMP': round(payslip.get_salary_line_total('MEAL_V_EMP'), 2),
            'ATN.CAR.2': round(payslip.get_salary_line_total('ATN.CAR.2'), 2),
            'ATN.INT.2': round(payslip.get_salary_line_total('ATN.INT.2'), 2),
            'ATN.MOB.2': round(payslip.get_salary_line_total('ATN.MOB.2'), 2),
            'NET': round(payslip.get_salary_line_total('NET'), 2),
            'holidays_compensation': round(new_contract.holidays_compensation, 2),
            'wage_with_holidays': round(new_contract.wage_with_holidays, 2),
            'company_car_total_depreciated_cost': round(new_contract.company_car_total_depreciated_cost, 2),
            'thirteen_month': round(new_contract.thirteen_month, 2),
            'double_holidays': round(new_contract.double_holidays, 2),
        })

        if new_contract.transport_mode == "public_transport":
            transport_advantage = new_contract.public_transport_reimbursed_amount
        elif new_contract.transport_mode == "others":
            transport_advantage = new_contract.others_reimbursed_amount
        else:
            transport_advantage = new_contract.company_car_total_depreciated_cost

        thirteen_month_net = payslip.get_salary_line_total('NET')
        double_holidays_net = payslip.get_salary_line_total('NET') * 0.92

        monthly_nature = round(transport_advantage + new_contract.internet + new_contract.mobile + new_contract.mobile_plus, 2)
        monthly_cash = round(new_contract.warrant_value_employee / 12.0 + new_contract.meal_voucher_amount * 20.0 + new_contract.fuel_card, 2)
        yearly_cash = round(new_contract.eco_checks + thirteen_month_net + double_holidays_net, 2)
        monthly_total = round(monthly_nature + monthly_cash + yearly_cash / 12.0 + payslip.get_salary_line_total('NET') - new_contract.representation_fees, 2)

        result.update({
            'monthly_nature': monthly_nature,
            'monthly_cash': monthly_cash,
            'yearly_cash': yearly_cash,
            'monthly_total': monthly_total,
            'employee_total_cost': round(new_contract.final_yearly_costs, 2),
        })

        return result

    @http.route(['/salary_package/onchange_mobile/'], type='json', auth='public')
    def onchange_mobile(self, contract_id, advantages, **kw):
        amount = request.env['hr.contract'].sudo()._get_mobile_amount(advantages['has_mobile'], advantages['international_communication'])
        return {'mobile': amount}

    @http.route(['/salary_package/onchange_internet/'], type='json', auth='public')
    def onchange_internet(self, contract_id, advantages, **kw):
        amount = request.env['hr.contract'].sudo()._get_internet_amount(advantages['has_internet'])
        return {'internet': amount}

    @http.route(['/salary_package/onchange_car/'], type='json', auth='public')
    def onchange_car(self, car_option, vehicle_id, **kw):
        if car_option == "new":
            vehicle = request.env['fleet.vehicle.model'].sudo().browse(vehicle_id)
            co2 = vehicle.default_co2
            fuel_type = vehicle.default_fuel_type
            door_number = odometer = immatriculation = False
        else:
            vehicle = request.env['fleet.vehicle'].sudo().browse(vehicle_id)
            co2 = vehicle.co2
            fuel_type = vehicle.fuel_type
            door_number = vehicle.doors
            odometer = vehicle.odometer
            immatriculation = vehicle.acquisition_date
        return {'co2': co2, 'fuel_type': fuel_type, 'door_number': door_number, 'odometer': odometer, 'immatriculation': immatriculation}

    @http.route(['/salary_package/onchange_public_transport/'], type='json', auth='public')
    def onchange_public_transport(self, contract_id, advantages, **kw):
        amount = request.env['hr.contract'].sudo()._get_public_transport_reimbursed_amount(advantages['public_transport_employee_amount'])
        return {'amount': round(amount, 2)}

    @http.route(['/salary_package/submit/'], type='json', auth='public')
    def submit(self, contract_id=None, token=None, advantages=None, **kw):
        if token:
            contract = self._check_token_validity(token)
        else:
            contract = self._check_employee_access_right(contract_id)

        new_contract = self.create_new_contract(contract, advantages, no_write=True, **kw)

        if new_contract.id != contract.id:
            new_contract.write({
                'state': 'draft',
                'name': 'New contract - ' + new_contract.employee_id.name,
                'origin_contract_id': contract_id,
            })

        # Take specific contract to sign, or generic one on the job position
        if new_contract.signature_request_template_id:
            signature_request_template = new_contract.signature_request_template_id
        elif new_contract.employee_id.active:
            signature_request_template = new_contract.job_id.contract_update_template_id
        else:
            signature_request_template = new_contract.job_id.signature_request_template_id

        if not signature_request_template:
            return {'error': 1, 'error_msg': _('No signature template defined on the job position. Please contact the HR responsible.')}

        if not new_contract.job_id.hr_responsible_id:
            return {'error': 1, 'error_msg': _('No HR responsible defined on the job position. Please contact an administrator.')}

        res = request.env['signature.request'].sudo().initialize_new(
            signature_request_template.id,
            [
                {'role': request.env.ref('website_sign.signature_item_party_employee').id, 'partner_id': new_contract.employee_id.address_home_id.id},
                {'role': request.env.ref('hr_contract_salary.signature_item_party_job_responsible').id, 'partner_id': new_contract.job_id.hr_responsible_id.partner_id.id}
            ],
            [new_contract.job_id.hr_responsible_id.partner_id.id],
            'Signature Request - ' + new_contract.name,
            'Signature Request - ' + new_contract.name,
            '',
            False
        )

        items = request.env['signature.item'].sudo().search([
            ('template_id', '=', signature_request_template.id),
            ('name', '!=', '')
        ])
        for item in items:
            new_value = new_contract
            for elem in item.name.split('.'):
                if elem in new_value:
                    new_value = new_value[elem]
                else:
                    new_value = ''
                if elem == 'holidays':
                    new_value = new_value - 20.0
            if isinstance(new_value, models.BaseModel):
                new_value = ''
            if isinstance(new_value, float):
                new_value = round(new_value, 2)
            if new_value or (new_value == 0.0):
                request.env['signature.item.value'].sudo().create({
                    'signature_item_id': item.id,
                    'signature_request_id': res['id'],
                    'value': new_value,
                })

        signature_request = request.env['signature.request'].browse(res['id']).sudo()
        signature_request.toggle_favorited()
        signature_request.action_sent()
        signature_request.write({'state': 'sent'})
        signature_request.request_item_ids.write({'state': 'sent'})

        access_token = request.env['signature.request.item'].sudo().search([
            ('signature_request_id', '=', res['id']),
            ('role_id', '=', request.env.ref('website_sign.signature_item_party_employee').id)
        ]).access_token

        new_contract.signature_request_ids += signature_request

        return {'job_id': new_contract.job_id.id, 'request_id': res['id'], 'token': access_token, 'error': 0, 'new_contract_id': new_contract.id}


class WebsiteSign(WebsiteSign):

    @http.route(['/sign/sign/<int:id>/<token>'], type='json', auth='public')
    def sign(self, id, token, signature=None):
        result = super(WebsiteSign, self).sign(id, token, signature)
        request_item = request.env['signature.request.item'].sudo().search([('access_token', '=', token)])
        contract = request.env['hr.contract'].sudo().search([('signature_request_ids', 'in', request_item.signature_request_id.ids)])
        if contract:
            contract.access_token_consumed = True
            return {'url': '/salary_package/thank_you/' + str(contract.job_id.id)}
        return result
