# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo.http import request
from odoo import _


def _execute_sql_query(fields, tables, conditions, query_args, filters, groupby=None):
    """ Returns the result of the SQL query. """
    query, args = _build_sql_query(fields, tables, conditions, query_args, filters, groupby=groupby)
    request.cr.execute(query, args)
    return request.cr.dictfetchall()


def _build_sql_query(fields, tables, conditions, query_args, filters, groupby=None):
    """ The goal of this function is to avoid:
        * writing raw SQL requests (kind of abstraction)
        * writing additionnal conditions for filters (same conditions for every request)
    :params fields, tables, conditions: basic SQL request statements
    :params query_args: dict of optional query args used in the request
    :params filters: dict of optional filters (template_ids, tag_ids, company_ids)
    :params groupby: additionnal groupby statement

    :returns: the SQL request and the new query_args (with filters tables & conditions)
    """
    # The conditions should use named arguments and these arguments are in query_args.

    if filters.get('template_ids'):
        tables.append("sale_subscription")
        conditions.append("account_invoice_line.subscription_id = sale_subscription.id")
        conditions.append("sale_subscription.template_id IN %(template_ids)s")
        query_args['template_ids'] = tuple(filters.get('template_ids'))

    if filters.get('tag_ids'):
        tables.append("sale_subscription")
        tables.append("account_analytic_tag_sale_subscription_rel")
        conditions.append("account_invoice_line.subscription_id = sale_subscription.id")
        conditions.append("sale_subscription.id = account_analytic_tag_sale_subscription_rel.sale_subscription_id")
        conditions.append("account_analytic_tag_sale_subscription_rel.account_analytic_tag_id IN %(tag_ids)s")
        query_args['tag_ids'] = tuple(filters.get('tag_ids'))

    if filters.get('company_ids'):
        conditions.append("account_invoice.company_id IN %(company_ids)s")
        conditions.append("account_invoice_line.company_id IN %(company_ids)s")
        query_args['company_ids'] = tuple(filters.get('company_ids'))

    fields_str = ', '.join(set(fields))
    tables_str = ', '.join(set(tables))
    conditions_str = ' AND '.join(set(conditions))

    if groupby:
        base_query = "SELECT %s FROM %s WHERE %s GROUP BY %s" % (fields_str, tables_str, conditions_str, groupby)
    else:
        base_query = "SELECT %s FROM %s WHERE %s" % (fields_str, tables_str, conditions_str)

    return base_query, query_args


def compute_net_revenue(start_date, end_date, filters):
    fields = ['SUM(account_invoice_line.price_subtotal_signed)']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "account_invoice.date_invoice BETWEEN %(start_date)s AND %(end_date)s",
        "account_invoice_line.invoice_id = account_invoice.id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'start_date': start_date,
        'end_date': end_date,
    }, filters)

    return 0 if not sql_results or not sql_results[0]['sum'] else int(sql_results[0]['sum'])


def compute_arpu(start_date, end_date, filters):
    mrr = compute_mrr(start_date, end_date, filters)
    nb_customers = compute_nb_contracts(start_date, end_date, filters)
    result = 0 if not nb_customers else mrr/float(nb_customers)
    return int(result)


def compute_arr(start_date, end_date, filters):
    result = 12*compute_mrr(start_date, end_date, filters)
    return int(result)


def compute_ltv(start_date, end_date, filters):
    # LTV = Average Monthly Recurring Revenue Per Customer / User Churn Rate
    mrr = compute_mrr(start_date, end_date, filters)
    nb_contracts = compute_nb_contracts(start_date, end_date, filters)
    avg_mrr_per_customer = 0 if nb_contracts == 0 else mrr / float(nb_contracts)
    logo_churn = compute_logo_churn(start_date, end_date, filters)
    result = 0 if logo_churn == 0 else avg_mrr_per_customer/float(logo_churn)
    return int(result)


def compute_nrr(start_date, end_date, filters):
    fields = ['SUM(account_invoice_line.price_subtotal_signed)']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "(account_invoice.date_invoice BETWEEN %(start_date)s AND %(end_date)s)",
        "account_invoice_line.invoice_id = account_invoice.id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.asset_start_date IS NULL",
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'start_date': start_date,
        'end_date': end_date,
    }, filters)

    return 0 if not sql_results or not sql_results[0]['sum'] else int(sql_results[0]['sum'])


def compute_nb_contracts(start_date, end_date, filters):
    fields = ['COUNT(DISTINCT account_invoice_line.subscription_id) AS sum']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "date %(date)s BETWEEN account_invoice_line.asset_start_date AND account_invoice_line.asset_end_date",
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.subscription_id IS NOT NULL"
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'date': end_date,
    }, filters)

    return 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']


def compute_mrr(start_date, end_date, filters):
    fields = ['SUM(account_invoice_line.asset_mrr)']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "date %(date)s BETWEEN account_invoice_line.asset_start_date AND account_invoice_line.asset_end_date",
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')"
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'date': end_date,
    }, filters)

    return 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']


def compute_logo_churn(start_date, end_date, filters):

    fields = ['COUNT(DISTINCT account_invoice_line.subscription_id) AS sum']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "date %(date)s - interval '1 months' BETWEEN account_invoice_line.asset_start_date AND account_invoice_line.asset_end_date",
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.subscription_id IS NOT NULL"
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'date': end_date,
    }, filters)

    active_customers_1_month_ago = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

    fields = ['COUNT(DISTINCT account_invoice_line.subscription_id) AS sum']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "date %(date)s - interval '1 months' BETWEEN account_invoice_line.asset_start_date AND account_invoice_line.asset_end_date",
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.subscription_id IS NOT NULL",
        """NOT exists (
                    SELECT 1 from account_invoice_line ail
                    WHERE ail.subscription_id = account_invoice_line.subscription_id
                    AND (date %(date)s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                )
        """,
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'date': end_date,
    }, filters)

    resigned_customers = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

    return 0 if not active_customers_1_month_ago else 100*resigned_customers/float(active_customers_1_month_ago)


def compute_revenue_churn(start_date, end_date, filters):

    fields = ['SUM(account_invoice_line.asset_mrr) AS sum']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "date %(date)s - interval '1 months' BETWEEN account_invoice_line.asset_start_date AND account_invoice_line.asset_end_date",
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.subscription_id IS NOT NULL",
        """NOT exists (
                    SELECT 1 from account_invoice_line ail
                    WHERE ail.subscription_id = account_invoice_line.subscription_id
                    AND (date %(date)s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                )
        """
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'date': end_date,
    }, filters)

    churned_mrr = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']
    previous_month_mrr = compute_mrr(start_date, (end_date - relativedelta(months=+1)), filters)
    return 0 if previous_month_mrr == 0 else 100*churned_mrr/float(previous_month_mrr)


def compute_mrr_growth_values(start_date, end_date, filters):
    new_mrr = 0
    expansion_mrr = 0
    down_mrr = 0
    churned_mrr = 0
    net_new_mrr = 0

    # 1. NEW
    fields = ['SUM(account_invoice_line.asset_mrr) AS sum']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "date %(date)s BETWEEN account_invoice_line.asset_start_date AND account_invoice_line.asset_end_date",
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.subscription_id IS NOT NULL",
        """NOT exists (
                    SELECT 1 from account_invoice_line ail
                    WHERE ail.subscription_id = account_invoice_line.subscription_id
                    AND (date %(date)s - interval '1 months' BETWEEN ail.asset_start_date AND ail.asset_end_date)
                )
        """
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'date': end_date,
    }, filters)

    new_mrr = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

    # 2. DOWN & EXPANSION
    fields = ['account_invoice_line.subscription_id', 'SUM(account_invoice_line.asset_mrr) AS sum']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
    ]
    groupby = "account_invoice_line.subscription_id"

    subquery_1 = _build_sql_query(fields, tables, [
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.asset_start_date BETWEEN date %(date)s - interval '1 months' + interval '1 days' and date %(date)s"
    ], {'date': end_date}, filters, groupby=groupby)

    subquery_2 = _build_sql_query(fields, tables, [
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.asset_end_date BETWEEN date %(date)s - interval '1 months' + interval '1 days' and date %(date)s"
    ], {'date': end_date}, filters, groupby=groupby)

    computed_query = """
        SELECT old_line.subscription_id, old_line.sum AS old_sum, new_line.sum AS new_sum, (new_line.sum - old_line.sum) AS diff
        FROM ( """ + subquery_1[0] + """ ) AS new_line, ( """ + subquery_2[0] + """ ) AS old_line
        WHERE
            new_line.subscription_id IS NOT NULL AND
            old_line.subscription_id = new_line.subscription_id
    """
    request.cr.execute(computed_query, subquery_1[1])

    sql_results = request.cr.dictfetchall()
    for account in sql_results:
        if account['diff'] > 0:
            expansion_mrr += account['diff']
        else:
            down_mrr -= account['diff']

    # 3. CHURNED
    fields = ['SUM(account_invoice_line.asset_mrr)']
    tables = ['account_invoice_line', 'account_invoice']
    conditions = [
        "date %(date)s - interval '1 months' BETWEEN account_invoice_line.asset_start_date AND account_invoice_line.asset_end_date",
        "account_invoice.id = account_invoice_line.invoice_id",
        "account_invoice.type IN ('out_invoice', 'out_refund')",
        "account_invoice.state NOT IN ('draft', 'cancel')",
        "account_invoice_line.subscription_id IS NOT NULL",
        """NOT exists (
                    SELECT 1 from account_invoice_line ail
                    WHERE ail.subscription_id = account_invoice_line.subscription_id
                    AND (date %(date)s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                )
        """,
    ]

    sql_results = _execute_sql_query(fields, tables, conditions, {
        'date': end_date,
    }, filters)

    churned_mrr = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

    net_new_mrr = new_mrr - churned_mrr + expansion_mrr - down_mrr

    return {
        'new_mrr': new_mrr,
        'churned_mrr': -churned_mrr,
        'expansion_mrr': expansion_mrr,
        'down_mrr': -down_mrr,
        'net_new_mrr': net_new_mrr,
    }


STAT_TYPES = {
    'mrr': {
        'name': _('Monthly Recurring Revenue'),
        'code': 'mrr',
        'dir': 'up',
        'prior': 1,
        'type': 'last',
        'add_symbol': 'currency',
        'compute': compute_mrr
    },
    'net_revenue': {
        'name': _('Net Revenue'),
        'code': 'net_revenue',
        'dir': 'up',
        'prior': 2,
        'type': 'sum',
        'add_symbol': 'currency',
        'compute': compute_net_revenue
    },
    'nrr': {
        'name': _('Non-Recurring Revenue'),
        'code': 'nrr',
        'dir': 'up',  # 'down' if fees ?
        'prior': 3,
        'type': 'sum',
        'add_symbol': 'currency',
        'compute': compute_nrr
    },
    'arpu': {
        'name': _('Revenue per Subscription'),
        'code': 'arpu',
        'dir': 'up',
        'prior': 4,
        'type': 'last',
        'add_symbol': 'currency',
        'compute': compute_arpu
    },
    'arr': {
        'name': _('Annual Run-Rate'),
        'code': 'arr',
        'dir': 'up',
        'prior': 5,
        'type': 'last',
        'add_symbol': 'currency',
        'compute': compute_arr
    },
    'ltv': {
        'name': _('Lifetime Value'),
        'code': 'ltv',
        'dir': 'up',
        'prior': 6,
        'type': 'last',
        'add_symbol': 'currency',
        'compute': compute_ltv
    },
    'logo_churn': {
        'name': _('Logo Churn'),
        'code': 'logo_churn',
        'dir': 'down',
        'prior': 7,
        'type': 'last',
        'add_symbol': '%',
        'compute': compute_logo_churn
    },
    'revenue_churn': {
        'name': _('Revenue Churn'),
        'code': 'revenue_churn',
        'dir': 'down',
        'prior': 8,
        'type': 'last',
        'add_symbol': '%',
        'compute': compute_revenue_churn
    },
    'nb_contracts': {
        'name': _('Subscriptions'),
        'code': 'nb_contracts',
        'dir': 'up',
        'prior': 9,
        'type': 'last',
        'add_symbol': '',
        'compute': compute_nb_contracts
    },
}

FORECAST_STAT_TYPES = {
    'mrr_forecast': {
        'name': _('Forecasted Annual MRR Growth'),
        'code': 'mrr_forecast',
        'prior': 1,
        'add_symbol': 'currency',
    },
    'contracts_forecast': {
        'name': _('Forecasted Annual Subscriptions Growth'),
        'code': 'contracts_forecast',
        'prior': 2,
        'add_symbol': '',
    },
}
