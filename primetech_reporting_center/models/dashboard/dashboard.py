from odoo import api, models, fields
from datetime import date, timedelta
from collections import defaultdict
from dateutil.relativedelta import relativedelta

class PrimetechDashboard(models.AbstractModel):
    _name = 'primetech.dashboard'
    _description = 'PrimeTech Dashboard Service'


    def _sum_pos_orders(self, domain):
        if 'pos.order' not in self.env.registry:
            return 0.0
        return sum(self.env['pos.order'].search(domain).mapped('amount_total'))

    def _get_period_bounds(self, filters=None):
        filters = filters or {}
        today = date.today()
        period = filters.get('period', 'month')
        if period == 'today':
            return today, today
        if period == 'week':
            return today - timedelta(days=today.weekday()), today
        if period == 'year':
            return today.replace(month=1, day=1), today
        if period == 'quarter':
            quarter_month = ((today.month - 1) // 3) * 3 + 1
            return today.replace(month=quarter_month, day=1), today
        return today.replace(day=1), today


    def _categorize_journal(self, journal):
        label = f"{journal.name or ''} {journal.code or ''}".lower()
        if any(token in label for token in ('momo', 'mobile money', 'mtn')):
            return 'MOMO'
        if any(token in label for token in ('om', 'orange money', 'orange')):
            return 'OM'
        if any(token in label for token in ('cash', 'caisse', 'espèce', 'espece', 'espèces', 'especes')):
            return 'Espèce'
        if journal.type == 'bank' or any(token in label for token in ('bank', 'banque')):
            return 'Banque'
        if journal.type == 'cash':
            return 'Espèce'
        return 'Autres'

    def _group_amounts_by_journal_category(self, records, amount_field='amount'):
        grouped = defaultdict(float)
        for record in records:
            journal = record.journal_id
            grouped[self._categorize_journal(journal)] += getattr(record, amount_field, 0.0) or 0.0
        return [{'category': key, 'amount': value} for key, value in sorted(grouped.items())]

    def _period_filter_value(self, filters, key, default=None):
        filters = filters or {}
        return filters.get(key) or filters.get('kpi_filters', {}).get(key) or default or filters.get('period', 'month')

    def _period_domain(self, filters, field_name, key=None):
        period_filters = dict(filters or {})
        if key:
            period_filters['period'] = self._period_filter_value(filters, key, period_filters.get('period', 'month'))
        return self._get_date_domain(period_filters, field_name)

    def _get_pos_session_state(self, filters=None):
        filters = filters or {}
        if 'pos.session' not in self.env.registry:
            return {'opened': 0, 'closed': 0, 'opening_balance': 0.0, 'current_balance': 0.0, 'closing_balance': 0.0, 'sessions': []}
        sessions = self.env['pos.session'].search(self._get_date_domain(filters, 'start_at'), order='start_at desc, id desc', limit=8)
        opened = sessions.filtered(lambda session: session.state not in ('closed', 'closing_control'))
        closed = sessions.filtered(lambda session: session.state in ('closed', 'closing_control'))
        session_lines = []
        for session in sessions:
            orders_total = sum(session.order_ids.mapped('amount_total')) if hasattr(session, 'order_ids') else 0.0
            opening_balance = getattr(session, 'cash_register_balance_start', 0.0) or 0.0
            real_balance = getattr(session, 'cash_register_balance_end_real', 0.0) or 0.0
            theoretical_balance = getattr(session, 'cash_register_balance_end', 0.0) or opening_balance + orders_total
            journal = getattr(getattr(session, 'config_id', False), 'journal_id', False)
            is_closed = session.state in ('closed', 'closing_control')
            session_lines.append({
                'id': session.id,
                'name': session.config_id.name or session.name,
                'state': 'Clôturé' if is_closed else 'En cours',
                'raw_state': session.state,
                'status_class': 'closed' if is_closed else 'open',
                'user': session.user_id.name or '-',
                'cashier': session.user_id.name or '-',
                'journal': journal.display_name if journal else '-',
                'opening_date': fields.Datetime.to_string(session.start_at) if session.start_at else '-',
                'opening_balance': opening_balance,
                'current_balance': theoretical_balance,
                'closing_balance': real_balance,
                'balance': real_balance if is_closed else theoretical_balance,
                'orders_total': orders_total,
            })
        return {
            'opened': len(opened),
            'closed': len(closed),
            'opening_balance': sum(getattr(s, 'cash_register_balance_start', 0.0) or 0.0 for s in sessions),
            'current_balance': sum((getattr(s, 'cash_register_balance_end', 0.0) or 0.0) for s in sessions),
            'closing_balance': sum((getattr(s, 'cash_register_balance_end_real', 0.0) or 0.0) for s in closed),
            'sessions': session_lines,
        }

    @api.model
    def get_executive_overview(self, filters=None):
        filters = filters or {}
        start, end = self._get_period_bounds(filters)
        invoice_domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', start), ('invoice_date', '<=', end)]
        invoice_revenue = sum(self.env['account.move'].search(invoice_domain).mapped('amount_total'))
        pos_domain = [('date_order', '>=', start), ('date_order', '<=', fields.Datetime.to_string(fields.Datetime.now()))]
        pos_revenue = self._sum_pos_orders(pos_domain)
        revenue_total = invoice_revenue + pos_revenue
        purchase_total = sum(self.env['purchase.order'].search([('state', 'in', ['purchase', 'done']), ('date_approve', '>=', start)]).mapped('amount_total'))
        stock_value = sum(product.qty_available * product.standard_price for product in self.env['product.product'].search([]))
        return {
            'period_label': {'today': "Aujourd'hui", 'week': 'Cette semaine', 'month': 'Ce mois', 'quarter': 'Ce trimestre', 'year': 'Cette année'}.get(filters.get('period', 'month'), 'Ce mois'),
            'revenue_total': revenue_total,
            'invoice_revenue': invoice_revenue,
            'pos_revenue': pos_revenue,
            'gross_margin': revenue_total - purchase_total,
            'purchase_total': purchase_total,
            'stock_value': stock_value,
            'bank_balance': sum(self.env['account.account'].search([('account_type', '=', 'asset_cash')]).mapped('current_balance')),
            'cash_registers': self._get_pos_session_state({'period': self._period_filter_value(filters, 'cash_period', filters.get('period', 'today'))}),
            'stock_alerts': {
                'out_of_stock': self.env['product.product'].search_count([('qty_available', '<=', 0), ('type', '=', 'product')]),
                'pending_transfers': self.env['stock.picking'].search_count([('state', 'not in', ('done', 'cancel'))]),
            },
            'hr': {
                'employees': self.env['hr.employee'].search_count([]) if 'hr.employee' in self.env.registry else 0,
                'on_leave': self.env['hr.leave'].search_count([('state', '=', 'validate')]) if 'hr.leave' in self.env.registry else 0,
            },
        }


    @api.model
    def get_executive_detail_sections(self, filters=None):
        filters = filters or {}
        overview = self.get_executive_overview(filters)
        sales_orders = self.env['sale.order'].search_count([('state', 'in', ('sale', 'done'))]) if 'sale.order' in self.env.registry else 0
        pending_deliveries = self.env['stock.picking'].search_count([('picking_type_code', '=', 'outgoing'), ('state', 'not in', ('done', 'cancel'))])
        pending_receipts = self.env['stock.picking'].search_count([('picking_type_code', '=', 'incoming'), ('state', 'not in', ('done', 'cancel'))])
        vendor_bills = self.env['account.move'].search_count([('move_type', '=', 'in_invoice'), ('state', '=', 'draft')])
        return {
            'sections': [
                {
                    'key': 'director',
                    'title': 'Direction Générale',
                    'subtitle': 'Vue globale, rentabilité, alertes',
                    'icon': 'fa fa-dashboard',
                    'action': 'primetech_reporting_center.action_primetech_reporting_dashboard',
                    'tone': 'black',
                    'metrics': [
                        {'label': 'CA temps réel', 'value': overview['revenue_total'], 'format': 'currency'},
                        {'label': 'Marge brute', 'value': overview['gross_margin'], 'format': 'currency'},
                        {'label': 'Banque', 'value': overview['bank_balance'], 'format': 'currency'},
                        {'label': 'Alertes stock', 'value': overview['stock_alerts']['out_of_stock'], 'format': 'number'},
                    ],
                },
                {
                    'key': 'finance',
                    'title': 'Finances & Comptabilité',
                    'subtitle': 'Trésorerie, dépenses, paiements, journaux',
                    'icon': 'fa fa-university',
                    'action': actions['finance'],
                    'tone': 'white',
                    'metrics': [
                        {'label': 'Situation bancaire', 'value': overview['bank_balance'], 'format': 'currency'},
                        {'label': 'Achats validés', 'value': overview['purchase_total'], 'format': 'currency'},
                        {'label': 'Factures fournisseurs', 'value': vendor_bills, 'format': 'number'},
                        {'label': 'Factures fournisseurs', 'value': vendor_bills, 'format': 'number'},
                    ],
                },
                {
                    'key': 'sales_cash',
                    'title': 'Ventes, PDV & Caisses',
                    'subtitle': 'Facturation, encaissement, ouverture/clôture',
                    'icon': 'fa fa-credit-card',
                    'action': actions['sales'],
                    'tone': 'black',
                    'metrics': [
                        {'label': 'Facturation', 'value': overview['invoice_revenue'], 'format': 'currency'},
                        {'label': 'Ventes PDV', 'value': overview['pos_revenue'], 'format': 'currency'},
                        {'label': 'Caisses ouvertes', 'value': overview['cash_registers']['opened'], 'format': 'number'},
                        {'label': 'Solde courant', 'value': overview['cash_registers']['current_balance'], 'format': 'currency'},
                    ],
                },
                {
                    'key': 'stock_supply',
                    'title': 'Stocks & Supply Chain',
                    'subtitle': 'Magasins, transferts, livraisons, ruptures',
                    'icon': 'fa fa-truck',
                    'action': out_action,
                    'tone': 'white',
                    'metrics': [
                        {'label': 'Valeur stock', 'value': overview['stock_value'], 'format': 'currency'},
                        {'label': 'Ruptures', 'value': overview['stock_alerts']['out_of_stock'], 'format': 'number'},
                        {'label': 'Transferts', 'value': overview['stock_alerts']['pending_transfers'], 'format': 'number'},
                        {'label': 'Livraisons', 'value': pending_deliveries, 'format': 'number'},
                    ],
                },
                {
                    'key': 'operations',
                    'title': 'Exploitation & Boutiques',
                    'subtitle': 'Rayons, réserves, préparations, demandes',
                    'icon': 'fa fa-sitemap',
                    'action': actions['transfers'],
                    'tone': 'black',
                    'metrics': [
                        {'label': 'Commandes clients', 'value': sales_orders, 'format': 'number'},
                        {'label': 'Réceptions', 'value': pending_receipts, 'format': 'number'},
                        {'label': 'Réceptions', 'value': pending_receipts, 'format': 'number'},
                        {'label': 'Préparations', 'value': pending_deliveries, 'format': 'number'},
                    ],
                },
                {
                    'key': 'hr_admin',
                    'title': 'RH, Rapports & Administration',
                    'subtitle': 'Effectifs, rapports, audit, paramétrage',
                    'icon': 'fa fa-shield',
                    'action': 'primetech_reporting_center.action_hr_overview_dashboard',
                    'tone': 'white',
                    'metrics': [
                        {'label': 'Effectif', 'value': overview['hr']['employees'], 'format': 'number'},
                        {'label': 'Congés validés', 'value': overview['hr']['on_leave'], 'format': 'number'},
                        {'label': 'Rapports', 'value': 13, 'format': 'number'},
                        {'label': 'Audit système', 'value': 1, 'format': 'number'},
                    ],
                },
            ],
            'focus': [
                {'label': 'Solde courant caisses', 'value': overview['cash_registers']['current_balance'], 'format': 'currency', 'action': actions['finance']},
                {'label': 'Solde clôturé caisses', 'value': overview['cash_registers']['closing_balance'], 'format': 'currency', 'action': actions['finance']},
                {'label': 'Achats validés', 'value': overview['purchase_total'], 'format': 'currency', 'action': actions['purchase']},
                {'label': 'Congés validés', 'value': overview['hr']['on_leave'], 'format': 'number', 'action': 'primetech_reporting_center.action_hr_overview_dashboard'},
            ],
        }


    @api.model
    def get_executive_board(self, filters=None):
        filters = filters or {}
        overview = self.get_executive_overview(filters)
        # Fallback to all-system data if the selected period has no revenue, so
        # the executive board remains useful on databases without today's data.
        if not overview.get('revenue_total'):
            invoice_revenue = sum(self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]).mapped('amount_total'))
            pos_revenue = self._sum_pos_orders([])
            purchase_total = sum(self.env['purchase.order'].search([('state', 'in', ['purchase', 'done'])]).mapped('amount_total'))
            overview.update({
                'revenue_total': invoice_revenue + pos_revenue,
                'invoice_revenue': invoice_revenue,
                'pos_revenue': pos_revenue,
                'purchase_total': purchase_total,
                'gross_margin': invoice_revenue + pos_revenue - purchase_total,
            })
        StockPicking = self.env['stock.picking']
        Product = self.env['product.product']
        ProductTemplate = self.env['product.template']

        def open_model(name, model, domain=None, context=None, views=None):
            view_mode = views or 'list,form'
            return {
                'type': 'ir.actions.act_window',
                'name': name,
                'res_model': model,
                'view_mode': view_mode,
                'views': [[False, mode] for mode in view_mode.split(',')],
                'domain': domain or [],
                'context': context or {},
            }

        selected_period = filters.get('period', 'month')
        period_labels = {'today': "Aujourd'hui", 'week': 'Cette semaine', 'month': 'Ce mois', 'quarter': 'Ce trimestre', 'year': 'Cette année'}
        period_label = period_labels.get(selected_period, 'Ce mois')
        store_period = self._period_filter_value(filters, 'store_period', selected_period)
        revenue_period = self._period_filter_value(filters, 'revenue_period', selected_period)
        store_label = period_labels.get(store_period, period_label)
        revenue_label = period_labels.get(revenue_period, period_label)
        start, end = self._get_period_bounds({'period': selected_period})
        store_start, store_end = self._get_period_bounds({'period': store_period})
        revenue_start, revenue_end = self._get_period_bounds({'period': revenue_period})
        sale_report_domain = [('date', '>=', start), ('date', '<=', end)]
        actions = {
            'sales': open_model(
                'Analyse du chiffre d\'affaires',
                'sale.report',
                sale_report_domain,
                {'group_by': ['date:year', 'date:month', 'date:day']},
                'pivot,graph,list',
            ),
            'finance': open_model('Situation financière', 'account.move', [], {'search_default_posted': 1}),
            'purchase': open_model('Commandes fournisseurs', 'purchase.order', []),
            'stock': open_model('Stocks disponibles', 'stock.quant', [('location_id.usage', '=', 'internal')]),
            'transfers': open_model('Bons de transfert', 'stock.picking', []),
            'products': open_model('Produits', 'product.template', []),
        }
        if 'pos.order' in self.env.registry:
            actions['pos'] = open_model('Ventes PDV', 'pos.order', [])
        else:
            actions['pos'] = actions['sales']
        if 'pos.session' in self.env.registry:
            actions['pos_sessions'] = open_model('Sessions de caisse', 'pos.session', [])
        else:
            actions['pos_sessions'] = actions['pos']
        if 'hr.employee' in self.env.registry:
            actions['hr'] = open_model('Employés', 'hr.employee', [])
        else:
            actions['hr'] = actions['finance']

        receivable_kpis = self._get_partner_balance_kpis(open_model, filters)
        bank_period_filters = dict(filters, period=filters.get('period', 'month'))
        banks = []
        for journal in self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))]):
            journal_line_domain = [('journal_id', '=', journal.id), ('parent_state', '=', 'posted')] + self._get_date_domain(bank_period_filters, 'date')
            if journal.default_account_id:
                journal_line_domain.append(('account_id', '=', journal.default_account_id.id))
            journal_lines = self.env['account.move.line'].search(journal_line_domain)
            balance = sum(journal_lines.mapped('balance'))
            if balance <= 0:
                continue
            banks.append({
                'id': journal.id,
                'name': journal.display_name,
                'category': self._categorize_journal(journal),
                'balance': balance,
                'action': open_model(journal.display_name, 'account.move.line', journal_line_domain),
            })
        if 'pos.payment' in self.env.registry:
            pos_payment_domain = [
                ('pos_order_id.state', 'in', ('paid', 'done', 'invoiced')),
            ] + self._get_date_domain(bank_period_filters, 'payment_date')
            for group in self.env['pos.payment'].read_group(
                pos_payment_domain,
                ['amount:sum'],
                ['payment_method_id'],
                lazy=False,
            ):
                payment_method = group.get('payment_method_id')
                if not payment_method:
                    continue
                method_id, method_name = payment_method
                payment_total = group.get('amount', 0.0)
                if payment_total <= 0:
                    continue
                method_domain = pos_payment_domain + [('payment_method_id', '=', method_id)]
                banks.append({
                    'id': f'pos-payment-{method_id}',
                    'name': f'PDV — {method_name}',
                    'category': 'Point de vente',
                    'balance': payment_total,
                    'action': open_model(f'Paiements PDV — {method_name}', 'pos.payment', method_domain),
                })
        billing_period = self._period_filter_value(filters, 'billing_period', filters.get('period', 'month'))
        billing_filters = dict(filters, period=billing_period)
        invoice_domain_all = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')] + self._get_date_domain(billing_filters, 'invoice_date')
        posted_invoices = self.env['account.move'].search(invoice_domain_all)
        billing_total = sum(posted_invoices.mapped('amount_total'))
        billing_balance = sum(posted_invoices.mapped('amount_residual'))
        billing_paid = billing_total - billing_balance
        unpaid_invoice_domain = invoice_domain_all + [('payment_state', 'in', ['not_paid', 'partial'])]
        unpaid_invoice_count = self.env['account.move'].search_count(unpaid_invoice_domain)
        billing_count = len(posted_invoices)
        billing = {
            'period': billing_period,
            'total': billing_total,
            'paid': billing_paid,
            'balance': billing_balance,
            'count': billing_count,
            'unpaid_count': unpaid_invoice_count,
            'unpaid_rate': (billing_balance / billing_total * 100 if billing_total else 0),
            'action': open_model('Factures clients', 'account.move', invoice_domain_all, {'search_default_posted': 1}),
            'payments_action': open_model('Factures clients encaissées', 'account.move', invoice_domain_all + [('payment_state', 'in', ['paid', 'in_payment'])], {'search_default_posted': 1}),
            'unpaid_action': open_model('Factures clients impayées', 'account.move', unpaid_invoice_domain, {'search_default_posted': 1}),
        }
        confirmed_purchase_domain = [('state', 'in', ['purchase', 'done'])]
        purchase_group = self.env['purchase.order'].read_group(confirmed_purchase_domain, ['amount_total'], [])
        purchase_total_confirmed = purchase_group[0].get('amount_total', 0.0) if purchase_group else 0.0
        supplier_bill_domain = [('move_type', '=', 'in_invoice'), ('state', '=', 'posted')]
        supplier_bill_group = self.env['account.move'].read_group(supplier_bill_domain, ['amount_total', 'amount_residual'], [])
        supplier_bill_total = supplier_bill_group[0].get('amount_total', 0.0) if supplier_bill_group else 0.0
        supplier_debt_total = supplier_bill_group[0].get('amount_residual', 0.0) if supplier_bill_group else 0.0
        supplier_unpaid_count = self.env['account.move'].search_count(supplier_bill_domain + [('amount_residual', '>', 0)])
        supplier_payment_domain = [('payment_type', '=', 'outbound'), ('state', 'not in', ['draft', 'cancel', 'cancelled', 'rejected'])]
        supplier_payment_group = self.env['account.payment'].read_group(supplier_payment_domain, ['amount'], [])
        supplier_payment_total = supplier_payment_group[0].get('amount', 0.0) if supplier_payment_group else 0.0
        supplier_bill_paid_total = supplier_bill_total - supplier_debt_total
        supplier_payment_total = max(supplier_payment_total, supplier_bill_paid_total)
        supplier_action = open_model('Fournisseurs', 'res.partner', [('supplier_rank', '>', 0)])
        supplier_bills_action = open_model('Factures fournisseurs', 'account.move', supplier_bill_domain, {'search_default_posted': 1})
        supplier_payments_action = open_model('Paiements fournisseurs', 'account.payment', supplier_payment_domain)
        cash_lines = overview['cash_registers']['sessions'][:5]
        if not cash_lines:
            cash_lines = [{'name': 'Aucune caisse', 'state': '-', 'user': '-', 'cashier': '-', 'balance': 0, 'current_balance': 0, 'closing_balance': 0, 'orders_total': 0, 'status_class': 'muted', 'action': actions['pos_sessions']}]
        else:
            for line in cash_lines:
                line['action'] = open_model('Session de caisse', 'pos.session', [('id', '=', line['id'])])
        stock_scope = self._period_filter_value(filters, 'stock_scope', 'all')
        template_base_domain = []
        if stock_scope == 'sale':
            template_base_domain.append(('sale_ok', '=', True))
        elif stock_scope == 'purchase':
            template_base_domain.append(('purchase_ok', '=', True))
        template_count = ProductTemplate.search_count(template_base_domain)
        scoped_product_domain = []
        if template_base_domain:
            scoped_template_ids = ProductTemplate.search(template_base_domain).ids
            if not scoped_template_ids:
                template_base_domain = []
                template_count = ProductTemplate.search_count(template_base_domain)
            else:
                scoped_product_domain = [('product_tmpl_id', 'in', scoped_template_ids)]
        product_action = open_model('Produits stockables', 'product.template', template_base_domain)
        internal_quant_domain = [('location_id.usage', '=', 'internal')]
        if scoped_product_domain:
            scoped_product_ids = Product.search(scoped_product_domain).ids
            internal_quant_domain.append(('product_id', 'in', scoped_product_ids))
        Quant = self.env['stock.quant']
        quant_value_field = 'value' if 'value' in Quant._fields else 'inventory_value' if 'inventory_value' in Quant._fields else None
        quant_fields = ['quantity'] + ([quant_value_field] if quant_value_field else [])
        quant_groups = Quant.read_group(internal_quant_domain, quant_fields, ['product_id'], lazy=False)
        grouped_product_ids = [group['product_id'][0] for group in quant_groups if group.get('product_id')]
        grouped_products = Product.browse(grouped_product_ids)
        product_by_id = {product.id: product for product in grouped_products}
        qty_by_template = defaultdict(float)
        value_by_template = defaultdict(float)
        for group in quant_groups:
            product_data = group.get('product_id')
            if not product_data:
                continue
            product = product_by_id.get(product_data[0])
            if not product:
                continue
            template = product.product_tmpl_id
            quantity = group.get('quantity', 0.0) or 0.0
            qty_by_template[template.id] += quantity
            unit_cost = product.standard_price or template.standard_price or template.list_price or 0.0
            quant_value = group.get(quant_value_field, 0.0) if quant_value_field else 0.0
            value_by_template[template.id] += quant_value or quantity * unit_cost
        stock_value = sum(value_by_template.values())
        positive_template_ids = {template_id for template_id, quantity in qty_by_template.items() if quantity > 0}
        out_count = max(template_count - len(positive_template_ids), 0)
        settings = self.env['primetech.reporting.settings'].get_values()
        min_qty = settings['stock_min_alert_threshold']
        max_qty = settings['stock_overstock_threshold']
        min_template_ids = [template_id for template_id, quantity in qty_by_template.items() if 0 < quantity <= min_qty]
        over_template_ids = [template_id for template_id, quantity in qty_by_template.items() if quantity >= max_qty]
        min_count = len(min_template_ids)
        over_count = len(over_template_ids)
        out_domain = template_base_domain + [('qty_available', '<=', 0)]
        min_domain = template_base_domain + [('qty_available', '>', 0), ('qty_available', '<=', min_qty)]
        over_domain = template_base_domain + [('qty_available', '>=', max_qty)]
        out_action = open_model('Produits en rupture', 'product.template', out_domain)
        min_action = open_model('Produits sous stock minimum', 'product.template', min_domain)
        over_action = open_model('Produits en surstock', 'product.template', over_domain)
        category_revenue = defaultdict(float)
        category_ids = {}
        for line in self.env['account.move.line'].search([('move_id.move_type', '=', 'out_invoice'), ('move_id.state', '=', 'posted'), ('product_id', '!=', False)] + self._get_date_domain(filters, 'move_id.invoice_date')):
            category = line.product_id.categ_id
            category_name = category.display_name or 'Sans catégorie'
            category_revenue[category_name] += line.price_total
            category_ids[category_name] = category.id
        if 'pos.order.line' in self.env.registry:
            for line in self.env['pos.order.line'].search([('product_id', '!=', False)] + self._get_date_domain(filters, 'order_id.date_order')):
                category = line.product_id.categ_id
                category_name = category.display_name or 'Sans catégorie'
                category_revenue[category_name] += line.price_subtotal_incl
                category_ids[category_name] = category.id
        category_total = sum(category_revenue.values())
        categories = [
            {
                'name': name,
                'value': value,
                'percent': (value / category_total * 100 if category_total else 0),
                'action': open_model('Produits catégorie ' + name, 'product.product', [('categ_id', 'child_of', category_ids[name])] if category_ids.get(name) else []),
            }
            for name, value in sorted(category_revenue.items(), key=lambda kv: kv[1], reverse=True)[:6]
        ]

        warehouse_values = defaultdict(float)
        warehouse_actions = {}
        warehouses = self.env['stock.warehouse'].search([])
        warehouse_order_ids = defaultdict(set)
        sale_order_domain = [('state', 'in', ['sale', 'done']), ('date_order', '>=', store_start), ('date_order', '<', fields.Datetime.to_datetime(store_end) + timedelta(days=1))]
        if 'sale.order' in self.env.registry and 'stock.move' in self.env.registry:
            Move = self.env['stock.move']
            if 'sale_line_id' in Move._fields:
                move_domain = [('state', '=', 'done'), ('sale_line_id', '!=', False), ('date', '>=', store_start), ('date', '<', fields.Datetime.to_datetime(store_end) + timedelta(days=1))]
                groupby_fields = ['sale_line_id'] + (['picking_type_id'] if 'picking_type_id' in Move._fields else [])
                move_groups = Move.read_group(move_domain, ['sale_line_id'], groupby_fields, lazy=False)
                picking_type_ids = [group['picking_type_id'][0] for group in move_groups if group.get('picking_type_id')]
                picking_types = self.env['stock.picking.type'].browse(picking_type_ids) if picking_type_ids else self.env['stock.picking.type']
                warehouse_by_type = {picking_type.id: picking_type.warehouse_id for picking_type in picking_types if picking_type.warehouse_id}
                sale_line_ids = [group['sale_line_id'][0] for group in move_groups if group.get('sale_line_id')]
                sale_lines = self.env['sale.order.line'].browse(sale_line_ids)
                sale_line_by_id = {line.id: line for line in sale_lines}
                for group in move_groups:
                    line_data = group.get('sale_line_id')
                    if not line_data:
                        continue
                    line = sale_line_by_id.get(line_data[0])
                    if not line or not line.order_id:
                        continue
                    picking_type_data = group.get('picking_type_id')
                    warehouse = warehouse_by_type.get(picking_type_data[0]) if picking_type_data else line.order_id.warehouse_id
                    if warehouse:
                        warehouse_order_ids[warehouse.id].add(line.order_id.id)
                for warehouse_id, order_ids in warehouse_order_ids.items():
                    order_group = self.env['sale.order'].read_group([('id', 'in', list(order_ids))], ['amount_total'], [])
                    warehouse_values[warehouse_id] += order_group[0].get('amount_total', 0.0) if order_group else 0.0
        if 'sale.order' in self.env.registry and not warehouse_values:
            for group in self.env['sale.order'].read_group(sale_order_domain, ['amount_total'], ['warehouse_id'], lazy=False):
                warehouse_data = group.get('warehouse_id')
                if warehouse_data:
                    warehouse_values[warehouse_data[0]] += group.get('amount_total', 0.0) or 0.0
        if 'sale.order' in self.env.registry:
            for warehouse in warehouses:
                warehouse_actions[warehouse.id] = open_model('Ventes déstockées ' + warehouse.display_name, 'sale.order', [('id', 'in', list(warehouse_order_ids.get(warehouse.id, [])))] if warehouse_order_ids.get(warehouse.id) else sale_order_domain + [('warehouse_id', '=', warehouse.id)])
        if 'pos.order' in self.env.registry:
            pos_domain = [('date_order', '>=', store_start), ('date_order', '<', fields.Datetime.to_datetime(store_end) + timedelta(days=1))]
            pos_groups = self.env['pos.order'].read_group(pos_domain, ['amount_total'], ['config_id'], lazy=False)
            config_ids = [group['config_id'][0] for group in pos_groups if group.get('config_id')]
            configs = self.env['pos.config'].browse(config_ids) if 'pos.config' in self.env.registry else []
            config_by_id = {config.id: config for config in configs}
            for group in pos_groups:
                config_data = group.get('config_id')
                config = config_by_id.get(config_data[0]) if config_data else False
                warehouse = config.picking_type_id.warehouse_id if config and config.picking_type_id else False
                if warehouse:
                    warehouse_values[warehouse.id] += group.get('amount_total', 0.0) or 0.0
        max_store_value = max(list(warehouse_values.values()) or [0.0])
        tones = ['green', 'orange', 'blue', 'purple', 'cyan', 'pink', 'slate']
        stores = []
        for index, warehouse in enumerate(sorted(warehouses, key=lambda wh: warehouse_values.get(wh.id, 0.0), reverse=True)[:7]):
            value = warehouse_values.get(warehouse.id, 0.0)
            stores.append({
                'name': warehouse.display_name,
                'value': value,
                'percent': (value / max_store_value * 100 if max_store_value else 0),
                'tone': tones[index % len(tones)],
                'action': warehouse_actions.get(warehouse.id) or open_model('Opérations ' + warehouse.display_name, 'stock.picking', [('picking_type_id.warehouse_id', '=', warehouse.id)]),
            })

        chart_group = 'month' if revenue_period == 'year' else 'day'
        chart_keys = []
        current_key = revenue_start.replace(day=1) if chart_group == 'month' else revenue_start
        while current_key <= revenue_end:
            chart_keys.append(current_key)
            current_key = current_key + relativedelta(months=1) if chart_group == 'month' else current_key + timedelta(days=1)
        revenue_by_key = defaultdict(float)
        invoice_groupby = f'invoice_date:{chart_group}'
        for group in self.env['account.move'].read_group(
            [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', revenue_start), ('invoice_date', '<=', revenue_end)],
            ['amount_total'],
            [invoice_groupby],
            lazy=False,
        ):
            range_info = (group.get('__range') or {}).get(invoice_groupby) or {}
            date_from = range_info.get('from')
            if date_from:
                key_date = fields.Date.from_string(date_from[:10])
                revenue_by_key[key_date.replace(day=1) if chart_group == 'month' else key_date] += group.get('amount_total', 0.0) or 0.0
        if 'pos.order' in self.env.registry:
            pos_groupby = f'date_order:{chart_group}'
            for group in self.env['pos.order'].read_group(
                [('date_order', '>=', revenue_start), ('date_order', '<', fields.Datetime.to_datetime(revenue_end) + timedelta(days=1))],
                ['amount_total'],
                [pos_groupby],
                lazy=False,
            ):
                range_info = (group.get('__range') or {}).get(pos_groupby) or {}
                date_from = range_info.get('from')
                if date_from:
                    key_date = fields.Date.from_string(date_from[:10])
                    revenue_by_key[key_date.replace(day=1) if chart_group == 'month' else key_date] += group.get('amount_total', 0.0) or 0.0
        max_revenue_key = max(list(revenue_by_key.values()) or [0.0])
        revenue_chart = {
            'subtitle': revenue_label,
            'items': [
                {
                    'key': key.isoformat(),
                    'label': key.strftime('%m/%Y') if chart_group == 'month' else key.strftime('%d/%m'),
                    'value': revenue_by_key.get(key, 0.0),
                    'height': (revenue_by_key.get(key, 0.0) / max_revenue_key * 100 if max_revenue_key else 0),
                }
                for key in chart_keys
            ],
        }
        vehicles = []
        if 'fleet.vehicle' in self.env.registry:
            for vehicle in self.env['fleet.vehicle'].search([], limit=10):
                status = vehicle.state_id.name if vehicle.state_id else 'Disponible'
                vehicles.append({
                    'vehicle': vehicle.license_plate or vehicle.name or '-',
                    'type': vehicle.model_id.name if vehicle.model_id else '-',
                    'status': status,
                    'availability': 'Disponible' if status.lower() in ('disponible', 'registered') else status,
                    'action': open_model('Véhicule', 'fleet.vehicle', [('id', '=', vehicle.id)]),
                })
        if not vehicles:
            vehicles = [{'vehicle': '-', 'type': '-', 'status': 'Aucun véhicule', 'availability': '-'}]

        def count_action_item(label, model, domain, action_name=None):
            return {
                'label': label,
                'count': self.env[model].search_count(domain),
                'action': open_model(action_name or label, model, domain),
            }

        procurement_items = [
            count_action_item('En attente', 'purchase.order', [('state', 'in', ['draft', 'sent', 'to approve'])], 'Demandes d’approvisionnement en attente'),
            count_action_item('Validées', 'purchase.order', [('state', 'in', ['purchase', 'done'])], 'Demandes d’approvisionnement validées'),
            count_action_item('En préparation', 'stock.picking', [('picking_type_id.code', '=', 'incoming'), ('state', 'in', ['confirmed', 'assigned'])], 'Réceptions fournisseurs en préparation'),
            count_action_item('Expédiées', 'stock.picking', [('picking_type_id.code', '=', 'incoming'), ('state', 'in', ['waiting', 'confirmed', 'assigned'])], 'Réceptions fournisseurs attendues'),
            count_action_item('Réceptionnées', 'stock.picking', [('picking_type_id.code', '=', 'incoming'), ('state', '=', 'done')], 'Réceptions fournisseurs terminées'),
        ]
        transfer_items = [
            count_action_item('En attente', 'stock.picking', [('picking_type_id.code', '=', 'internal'), ('state', 'in', ['draft', 'waiting'])], 'Transferts en attente'),
            count_action_item('En préparation', 'stock.picking', [('picking_type_id.code', '=', 'internal'), ('state', '=', 'confirmed')], 'Transferts en préparation'),
            count_action_item('En cours', 'stock.picking', [('picking_type_id.code', '=', 'internal'), ('state', '=', 'assigned')], 'Transferts en cours'),
            count_action_item('Expédiés', 'stock.picking', [('picking_type_id.code', '=', 'internal'), ('state', 'in', ['assigned'])], 'Transferts expédiés'),
            count_action_item('Réceptionnés', 'stock.picking', [('picking_type_id.code', '=', 'internal'), ('state', '=', 'done')], 'Transferts réceptionnés'),
        ]
        customer_items = [
            count_action_item('À préparer', 'stock.picking', [('picking_type_id.code', '=', 'outgoing'), ('state', '=', 'confirmed')], 'Commandes clients à préparer'),
            count_action_item('En préparation', 'stock.picking', [('picking_type_id.code', '=', 'outgoing'), ('state', '=', 'assigned')], 'Commandes clients en préparation'),
            count_action_item('En cours livraison', 'stock.picking', [('picking_type_id.code', '=', 'outgoing'), ('state', 'in', ['waiting', 'assigned'])], 'Commandes clients en livraison'),
            count_action_item('Livrées', 'stock.picking', [('picking_type_id.code', '=', 'outgoing'), ('state', '=', 'done')], 'Commandes clients livrées'),
        ]
        purchase_pending_count = procurement_items[0]['count']
        transfer_pending_count = sum(item['count'] for item in transfer_items if item['label'] != 'Réceptionnés')

        expiry_template_ids = []
        if 'stock.lot' in self.env.registry:
            Lot = self.env['stock.lot']
            expiry_field = 'expiration_date' if 'expiration_date' in Lot._fields else 'life_date' if 'life_date' in Lot._fields else None
            if expiry_field:
                expiry_limit = fields.Date.today() + timedelta(days=30)
                expiry_lots = Lot.search([(expiry_field, '!=', False), (expiry_field, '<=', expiry_limit), ('product_id.product_tmpl_id', 'in', list(qty_by_template.keys()))])
                expiry_template_ids = list(set(expiry_lots.mapped('product_id.product_tmpl_id').ids))
        recent_move_template_ids = set(self.env['stock.move'].search([
            ('state', '=', 'done'),
            ('date', '>=', fields.Datetime.subtract(fields.Datetime.now(), days=90)),
            ('product_id.product_tmpl_id', 'in', list(qty_by_template.keys())),
        ]).mapped('product_id.product_tmpl_id').ids)
        slow_template_ids = [template_id for template_id, quantity in qty_by_template.items() if quantity > 0 and template_id not in recent_move_template_ids]
        expiry_action = open_model('Produits proches péremption', 'product.template', [('id', 'in', expiry_template_ids)])
        slow_action = open_model('Articles à faible rotation', 'product.template', [('id', 'in', slow_template_ids)])

        sold_qty_by_template = defaultdict(float)
        if 'sale.order.line' in self.env.registry:
            sale_groups = self.env['sale.order.line'].read_group(
                [('order_id.state', 'in', ['sale', 'done']), ('order_id.date_order', '>=', start), ('order_id.date_order', '<=', end), ('product_id', '!=', False)],
                ['product_uom_qty'],
                ['product_id'],
                lazy=False,
            )
            sale_products = Product.browse([group['product_id'][0] for group in sale_groups if group.get('product_id')])
            sale_product_by_id = {product.id: product for product in sale_products}
            for group in sale_groups:
                product_data = group.get('product_id')
                product = sale_product_by_id.get(product_data[0]) if product_data else False
                if product:
                    sold_qty_by_template[product.product_tmpl_id.id] += group.get('product_uom_qty', 0.0) or 0.0
        invoice_groups = self.env['account.move.line'].read_group(
            [('move_id.move_type', '=', 'out_invoice'), ('move_id.state', '=', 'posted'), ('move_id.invoice_date', '>=', start), ('move_id.invoice_date', '<=', end), ('product_id', '!=', False)],
            ['quantity'],
            ['product_id'],
            lazy=False,
        )
        invoice_products = Product.browse([group['product_id'][0] for group in invoice_groups if group.get('product_id')])
        invoice_product_by_id = {product.id: product for product in invoice_products}
        for group in invoice_groups:
            product_data = group.get('product_id')
            product = invoice_product_by_id.get(product_data[0]) if product_data else False
            if product:
                sold_qty_by_template[product.product_tmpl_id.id] += group.get('quantity', 0.0) or 0.0
        if 'pos.order.line' in self.env.registry:
            pos_groups = self.env['pos.order.line'].read_group(
                [('order_id.date_order', '>=', start), ('order_id.date_order', '<=', end), ('product_id', '!=', False)],
                ['qty'],
                ['product_id'],
                lazy=False,
            )
            pos_products = Product.browse([group['product_id'][0] for group in pos_groups if group.get('product_id')])
            pos_product_by_id = {product.id: product for product in pos_products}
            for group in pos_groups:
                product_data = group.get('product_id')
                product = pos_product_by_id.get(product_data[0]) if product_data else False
                if product:
                    sold_qty_by_template[product.product_tmpl_id.id] += group.get('qty', 0.0) or 0.0

        watch_rows = []
        for template_id, sold_qty in sorted(sold_qty_by_template.items(), key=lambda item: item[1], reverse=True):
            stock_qty = qty_by_template.get(template_id, ProductTemplate.browse(template_id).qty_available)
            if sold_qty <= 0 or stock_qty > max(min_qty, sold_qty * 0.35):
                continue
            template = ProductTemplate.browse(template_id)
            if stock_qty <= 0:
                status = 'Rupture'
                action = out_action
            elif stock_qty <= min_qty:
                status = 'Stock min.'
                action = min_action
            else:
                status = 'Baisse stock'
                action = product_action
            watch_rows.append({
                'product': template.display_name,
                'rayon': template.categ_id.display_name or '-',
                'status': status,
                'stock': stock_qty,
                'sold_qty': sold_qty,
                'action': action,
            })
            if len(watch_rows) >= 8:
                break

        alerts = [
            {'title': 'Rupture de stock', 'detail': f"{out_count} produits en rupture", 'time': '10:30', 'action': out_action, 'icon': 'fa fa-warning'},
            {'title': 'Stock minimum atteint', 'detail': f"{min_count} produits sous minimum", 'time': '10:15', 'action': min_action, 'icon': 'fa fa-level-down'},
            {'title': 'Demande d’approvisionnement', 'detail': f"{purchase_pending_count} demandes en attente", 'time': '09:45', 'action': procurement_items[0]['action'], 'icon': 'fa fa-clock-o'},
            {'title': 'Bon de transfert en attente', 'detail': f"{transfer_pending_count} bons à suivre", 'time': '09:30', 'action': actions['transfers'], 'icon': 'fa fa-exchange'},
            {'title': 'Paiement en attente', 'detail': f"{supplier_unpaid_count} factures fournisseurs à payer", 'time': '09:10', 'action': supplier_bills_action, 'icon': 'fa fa-money'},
        ]

        def fmt_datetime(value):
            if not value:
                return '—'
            return fields.Datetime.to_string(value)[:19].replace('-', '/')

        activity_candidates = []
        for order in self.env['purchase.order'].search([], order='write_date desc', limit=5):
            activity_candidates.append({
                'key': f'purchase.order-{order.id}',
                'sort_date': order.write_date or order.create_date,
                'date': fmt_datetime(order.write_date or order.create_date),
                'user': order.user_id.name or order.create_uid.name,
                'action': 'Bon de commande',
                'doc': order.name,
                'state': dict(order._fields['state'].selection).get(order.state, order.state),
                'action_ref': open_model('Bon de commande', 'purchase.order', [('id', '=', order.id)]),
            })
        for picking in self.env['stock.picking'].search([], order='write_date desc', limit=5):
            activity_candidates.append({
                'key': f'stock.picking-{picking.id}',
                'sort_date': picking.write_date or picking.create_date,
                'date': fmt_datetime(picking.write_date or picking.create_date),
                'user': picking.user_id.name or picking.create_uid.name,
                'action': 'Mouvement de stock',
                'doc': picking.name,
                'state': dict(picking._fields['state'].selection).get(picking.state, picking.state),
                'action_ref': open_model('Mouvement de stock', 'stock.picking', [('id', '=', picking.id)]),
            })
        for payment in self.env['account.payment'].search([], order='write_date desc', limit=5):
            activity_candidates.append({
                'key': f'account.payment-{payment.id}',
                'sort_date': payment.write_date or payment.create_date,
                'date': fmt_datetime(payment.write_date or payment.create_date),
                'user': payment.create_uid.name,
                'action': 'Paiement',
                'doc': payment.name or payment.display_name,
                'state': dict(payment._fields['state'].selection).get(payment.state, payment.state),
                'action_ref': open_model('Paiement', 'account.payment', [('id', '=', payment.id)]),
            })
        activities = sorted(activity_candidates, key=lambda item: item['sort_date'] or fields.Datetime.now(), reverse=True)[:5]

        audit = []
        if 'ir.logging' in self.env.registry:
            for log in self.env['ir.logging'].sudo().search([], order='create_date desc', limit=5):
                audit.append({
                    'key': f'ir.logging-{log.id}',
                    'date': fmt_datetime(log.create_date),
                    'user': log.create_uid.name,
                    'action': (log.message or log.name or log.type or '-')[:80],
                    'module': log.name or log.type or '-',
                })
        if not audit and 'mail.message' in self.env.registry:
            for message in self.env['mail.message'].search([], order='date desc', limit=5):
                audit.append({
                    'key': f'mail.message-{message.id}',
                    'date': fmt_datetime(message.date),
                    'user': message.author_id.name or message.create_uid.name,
                    'action': (message.subject or message.record_name or message.message_type or '-')[:80],
                    'module': message.model or '-',
                })

        audit_events = self.env['primetech.audit.event'].sudo().search([], order='event_date desc, id desc', limit=16)
        if audit_events:
            event_type_labels = dict(self.env['primetech.audit.event']._fields['event_type'].selection)
            event_styles = {
                'create': ('fa-plus-circle', 'success', 'Créé'),
                'write': ('fa-pencil', 'warning', 'Modifié'),
                'unlink': ('fa-times-circle', 'danger', 'Supprimé'),
                'print': ('fa-print', 'info', 'Imprimé'),
                'event': ('fa-bolt', 'purple', 'Événement'),
            }
            activities = []
            audit = []
            for event in audit_events[:8]:
                icon, tone, status = event_styles.get(event.event_type, ('fa-circle', 'info', event_type_labels.get(event.event_type, event.event_type)))
                event_action = open_model(
                    event.document_name or event.model_label,
                    event.model_name,
                    [('id', '=', event.res_id)],
                ) if event.res_id and event.model_name in self.env.registry else False
                activities.append({
                    'key': f'audit-event-activity-{event.id}',
                    'sort_date': event.event_date,
                    'date': fmt_datetime(event.event_date),
                    'user': event.user_id.name,
                    'role': event.user_role or 'Utilisateur',
                    'action': event.action_label,
                    'description': event.details or event.action_label,
                    'doc': event.document_name or '-',
                    'state': status,
                    'tone': tone,
                    'icon': icon,
                    'action_ref': event_action,
                })
                audit.append({
                    'key': f'audit-event-{event.id}',
                    'date': fmt_datetime(event.event_date),
                    'user': event.user_id.name,
                    'role': event.user_role or 'Utilisateur',
                    'action': event.action_label,
                    'description': event.details or event.action_label,
                    'module': event.model_label,
                    'ip': event.ip_address or '-',
                    'device': event.device_info or '-',
                    'tone': tone,
                    'icon': icon,
                    'action_ref': event_action,
                })

        perf_start = fields.Datetime.to_datetime(start)
        perf_end = fields.Datetime.to_datetime(end) + timedelta(days=1)
        perf_done_pickings = StockPicking.search([('state', '=', 'done'), ('date_done', '>=', perf_start), ('date_done', '<', perf_end)])
        perf_recent_pickings = StockPicking.search([('create_date', '>=', perf_start), ('create_date', '<', perf_end), ('state', '!=', 'cancel')])
        perf_cancelled = StockPicking.search_count([('create_date', '>=', perf_start), ('create_date', '<', perf_end), ('state', '=', 'cancel')])
        delay_hours = [
            (picking.date_done - picking.scheduled_date).total_seconds() / 3600.0
            for picking in perf_done_pickings
            if picking.date_done and picking.scheduled_date
        ]
        service_rate = round(len(perf_done_pickings) / len(perf_recent_pickings) * 100, 1) if perf_recent_pickings else 0
        rupture_rate = round(out_count / template_count * 100, 2) if template_count else 0
        delivery_delay = round(sum(delay_hours) / len(delay_hours), 1) if delay_hours else 0
        error_rate = round(perf_cancelled / (len(perf_recent_pickings) + perf_cancelled) * 100, 2) if (perf_recent_pickings or perf_cancelled) else 0
        performance = [
            {'label': 'Taux de service', 'value': f'{service_rate}%', 'trend': period_label, 'tone': 'blue', 'percent': min(max(service_rate, 0), 100)},
            {'label': 'Taux de rupture', 'value': f'{rupture_rate}%', 'trend': f'{out_count} produits', 'tone': 'orange', 'percent': min(max(rupture_rate, 0), 100)},
            {'label': 'Délai moyen livraison', 'value': f'{delivery_delay} h', 'trend': period_label, 'tone': 'green', 'percent': min(max(delivery_delay / 24 * 100, 0), 100)},
            {'label': 'Taux d’erreur préparation', 'value': f'{error_rate}%', 'trend': f'{perf_cancelled} annulés', 'tone': 'purple', 'percent': min(max(error_rate, 0), 100)},
        ]
        history_action = open_model(
            'Historique complet des activités et événements',
            'primetech.audit.event',
            [],
            {'search_default_group_day': 0},
        )
        activity_history_action = history_action
        audit_history_action = history_action
        warehouse_load = []
        max_load_units = 0
        for warehouse in warehouses:
            prep_count = StockPicking.search_count([('picking_type_id.warehouse_id', '=', warehouse.id), ('state', '=', 'assigned')])
            order_count = StockPicking.search_count([('picking_type_id.warehouse_id', '=', warehouse.id), ('state', 'in', ['confirmed', 'waiting'])])
            max_load_units = max(max_load_units, prep_count + order_count)
            warehouse_load.append({
                'name': warehouse.display_name,
                'prep': prep_count,
                'orders': order_count,
                'load_units': prep_count + order_count,
                'action': open_model('Charge ' + warehouse.display_name, 'stock.picking', [('picking_type_id.warehouse_id', '=', warehouse.id), ('state', 'not in', ['done', 'cancel'])]),
            })
        for line in warehouse_load:
            line['load'] = (line['load_units'] / max_load_units * 100 if max_load_units else 0)
        warehouse_load = sorted(warehouse_load, key=lambda line: line['load_units'], reverse=True)[:8]
        return {
            'kpis': [
                {'label': "Chiffre d'affaires", 'value': overview['revenue_total'], 'suffix': 'FCFA', 'trend': '+12,5% vs hier', 'icon': 'fa fa-line-chart', 'tone': 'green', 'action': actions['sales']},
                {'label': 'Marge brute', 'value': overview['gross_margin'], 'suffix': 'FCFA', 'trend': '30,86%', 'icon': 'fa fa-pie-chart', 'tone': 'orange', 'action': actions['sales']},
                {'label': 'Résultat journalier', 'value': overview['gross_margin'] / 30 if overview['gross_margin'] else 0, 'suffix': 'FCFA', 'trend': '+8,3% vs hier', 'icon': 'fa fa-cog', 'tone': 'blue', 'action': actions['finance']},
                {'label': 'Total factures', 'value': billing['total'], 'suffix': 'FCFA', 'trend': billing_period.capitalize(), 'icon': 'fa fa-file-text-o', 'tone': 'purple', 'action': billing['action']},
                {'label': 'Créances clients', 'value': billing['balance'], 'suffix': 'FCFA', 'trend': 'Solde à encaisser', 'icon': 'fa fa-money', 'tone': 'pink', 'action': billing['action']},
                {'label': 'Achats fournisseurs', 'value': purchase_total_confirmed, 'suffix': 'FCFA', 'trend': 'Commandes confirmées', 'icon': 'fa fa-shopping-cart', 'tone': 'cyan', 'action': actions['purchase']},
                {'label': 'Factures fournisseurs', 'value': supplier_bill_total, 'suffix': 'FCFA', 'trend': 'Factures postées', 'icon': 'fa fa-file-text', 'tone': 'indigo', 'action': supplier_bills_action},
                {'label': 'Dettes fournisseurs', 'value': supplier_debt_total, 'suffix': 'FCFA', 'trend': 'Solde à payer', 'icon': 'fa fa-credit-card', 'tone': 'teal', 'action': supplier_bills_action},
                {'label': 'Paiements fournisseurs', 'value': supplier_payment_total, 'suffix': 'FCFA', 'trend': 'Paiements postés', 'icon': 'fa fa-bank', 'tone': 'red', 'action': supplier_payments_action},
                {'label': 'Fournisseurs actifs', 'value': self.env['res.partner'].search_count([('supplier_rank', '>', 0)]), 'suffix': '', 'trend': 'Référentiel', 'icon': 'fa fa-users', 'tone': 'slate', 'action': supplier_action},
            ],
            'stores': stores,
            'partner_balance_kpis': receivable_kpis,
            'store_period': store_period,
            'store_period_label': store_label,
            'revenue_chart': revenue_chart,
            'revenue_period': revenue_period,
            'period_label': period_label,
            'performance_period_label': period_label,
            'cash': cash_lines,
            'banks': banks,
            'billing': billing,
            'categories': {'total': category_total, 'items': categories},
            'current_user': {'name': self.env.user.name, 'status': 'En ligne'},
            'stock': {
                'value': stock_value,
                'scope': stock_scope,
                'products': template_count,
                'ruptures': out_count,
                'minimum': min_count,
                'overstock': over_count,
                'actions': {'products': product_action, 'ruptures': out_action, 'minimum': min_action, 'overstock': over_action},
            },
            'alerts': alerts,
            'settings': settings,
            'quick_actions': [
                {'label': "Créer une demande d’approvisionnement", 'icon': 'fa fa-cart-plus', 'action': actions['purchase']},
                {'label': 'Créer un bon de transfert', 'icon': 'fa fa-truck', 'action': actions['transfers']},
                {'label': 'Nouveau devis client', 'icon': 'fa fa-file-text-o', 'action': open_model('Nouveau devis client', 'account.move', [('move_type', '=', 'out_invoice')])},
                {'label': 'Nouveau bon de commande', 'icon': 'fa fa-shopping-cart', 'action': actions['purchase']},
                {'label': 'Nouveau produit', 'icon': 'fa fa-cube', 'action': actions['products']},
                {'label': 'Rapport de vente', 'icon': 'fa fa-bar-chart', 'action': actions['sales']},
            ],
            'supply': {
                'requests': {'total': sum(item['count'] for item in procurement_items), 'items': procurement_items},
                'transfers': {'total': sum(item['count'] for item in transfer_items), 'items': transfer_items},
                'customers': {'total': sum(item['count'] for item in customer_items), 'items': customer_items},
            },
            'warehouse_load': warehouse_load,
            'logistics_alerts': [
                {'label': 'Rupture de stock', 'value': out_count, 'tone': 'danger', 'action': out_action},
                {'label': 'Stock minimum atteint', 'value': min_count, 'tone': 'warn', 'action': min_action},
                {'label': 'Surstock', 'value': over_count, 'tone': 'ok', 'action': over_action},
                {'label': 'Stock proche péremption', 'value': len(expiry_template_ids), 'tone': 'info', 'action': expiry_action},
                {'label': 'Articles à faible rotation', 'value': len(slow_template_ids), 'tone': 'warn', 'action': slow_action},
            ],
            'vehicles': vehicles,
            'drivers': [{'driver': e.name, 'vehicle': '-', 'status': 'Disponible' if e.active else 'Inactif', 'next': '—', 'action': open_model('Chauffeur', 'hr.employee', [('id', '=', e.id)])} for e in (self.env['hr.employee'].search(['|', ('job_id.name', 'ilike', 'chauffeur'), ('job_title', 'ilike', 'chauffeur')], limit=10) if 'hr.employee' in self.env.registry else [])],
            'top_watch': watch_rows,
            'audit': audit,
            'activities': activities,
            'performance': performance,
            'activity_history_action': activity_history_action,
            'audit_history_action': audit_history_action,
        }

    def _get_partner_balance_kpis(self, open_model, filters=None):
        filters = filters or {}
        kpi_filters = filters.get('kpi_filters', {}) or {}
        AccountMoveLine = self.env['account.move.line']
        included_account_types = ['asset_receivable', 'liability_payable']
        extra_account_ids = self._get_partner_balance_extra_account_ids()
        base_domain = [('partner_id', '!=', False), ('display_type', 'not in', ('line_section', 'line_note'))]
        partner_search = filters.get('partner_search', {}) or {}
        search_type = filters.get('partner_search_type')
        search_term = (partner_search.get(search_type) or '').strip() if search_type in ('customers', 'suppliers') else ''
        if search_term:
            # Resolve names on the much smaller partner table first. Filtering the
            # ledger with partner IDs then uses account_move_line.partner_id's
            # index instead of an expensive ILIKE join over the complete ledger.
            matching_partner_ids = self.env['res.partner'].with_context(active_test=False).search(
                [('name', 'ilike', search_term)],
                limit=100,
            ).ids
            if not matching_partner_ids:
                return {
                    search_type: {
                        'title': 'Top créances client' if search_type == 'customers' else 'Top créances fournisseur',
                        'total': 0.0,
                        'count': 0,
                        'filtered_count': 0,
                        'rows': [],
                        'action': {},
                    },
                }
            base_domain.append(('partner_id', 'in', matching_partner_ids))
        balance_domain = base_domain + [
            '|',
            ('account_id.account_type', 'in', included_account_types),
            ('account_id', 'in', extra_account_ids or [0]),
        ]

        grouped = AccountMoveLine.read_group(
            balance_domain,
            ['debit:sum', 'credit:sum', 'balance:sum'],
            ['partner_id'],
            lazy=False,
        )
        partner_rows = {}
        for group in grouped:
            partner_data = group.get('partner_id')
            if not partner_data:
                continue
            partner_rows[partner_data[0]] = {
                'partner_id': partner_data[0],
                'partner': partner_data[1],
                'debit': group.get('debit') or 0.0,
                'credit': group.get('credit') or 0.0,
                'raw_balance': group.get('balance') or 0.0,
            }

        def add_balance(partner, debit=0.0, credit=0.0):
            if not partner:
                return
            row = partner_rows.setdefault(partner.id, {
                'partner_id': partner.id,
                'partner': partner.display_name,
                'debit': 0.0,
                'credit': 0.0,
                'raw_balance': 0.0,
            })
            row['debit'] += debit
            row['credit'] += credit
            row['raw_balance'] += debit - credit

        if 'account.payment' in self.env.registry:
            Payment = self.env['account.payment']
            payment_domain = [('partner_id', '!=', False)]
            if search_term:
                payment_domain.append(('partner_id', 'in', matching_partner_ids))
            if 'state' in Payment._fields:
                payment_domain.append(('state', 'not in', ('draft', 'cancel', 'cancelled')))
            for payment in Payment.search(payment_domain):
                move = payment.move_id if 'move_id' in Payment._fields else False
                if move and move.line_ids:
                    continue
                amount = payment.amount or 0.0
                if not amount:
                    continue
                if payment.payment_type == 'inbound':
                    add_balance(payment.partner_id, credit=amount)
                elif payment.payment_type == 'outbound':
                    add_balance(payment.partner_id, debit=amount)

        statement_domain = [('partner_id', '!=', False)]
        if search_term:
            statement_domain.append(('partner_id', 'in', matching_partner_ids))
        if 'account.bank.statement.line' in self.env.registry:
            BankStatementLine = self.env['account.bank.statement.line']
            if 'move_id' in BankStatementLine._fields:
                statement_domain.append(('move_id', '=', False))
            for statement in BankStatementLine.search(statement_domain):
                amount = statement.amount or 0.0
                if not amount:
                    continue
                if amount < 0:
                    add_balance(statement.partner_id, debit=abs(amount))
                else:
                    add_balance(statement.partner_id, credit=amount)

        def filtered_rows(rows, filter_key, balance_sign):
            if filter_key == 'high':
                total = sum(row['balance'] for row in rows)
                average = total / len(rows) if rows else 0.0
                threshold = max(total * 0.10, average)
                return [row for row in rows if row['balance'] >= threshold]
            if filter_key == 'with_debit':
                return [row for row in rows if row['debit'] > 0]
            if filter_key == 'with_credit':
                return [row for row in rows if row['credit'] > 0]
            if filter_key == 'without_payment':
                payment_field = 'credit' if balance_sign == 1 else 'debit'
                return [row for row in rows if row[payment_field] <= 0]
            return rows

        def build_kpi(title, balance_sign, filter_key, search_key):
            search_term = (partner_search.get(search_key) or '').strip().casefold()
            rows = []
            for partner_id, values in partner_rows.items():
                balance = values['raw_balance'] * balance_sign
                # A named search covers the complete receivables ledger, including
                # fully settled partners. Without a search, keep the KPI semantic
                # and rank only partners with an outstanding positive balance.
                if balance < 0 or (not search_term and balance == 0):
                    continue
                partner_domain_line = balance_domain + [('partner_id', '=', partner_id)]
                rows.append({
                    'partner_id': partner_id,
                    'partner': values['partner'],
                    'debit': values['debit'],
                    'credit': values['credit'],
                    'balance': balance,
                    'action': open_model(
                        f"{title} - {values['partner']}",
                        'account.move.line',
                        partner_domain_line,
                        {'group_by': ['partner_id']},
                        'list,pivot,graph',
                    ),
                })
            rows = sorted(rows, key=lambda row: row['balance'], reverse=True)
            positive_rows = [row for row in rows if row['balance'] > 0]
            global_total = sum(row['balance'] for row in positive_rows)
            filtered = filtered_rows(rows, filter_key, balance_sign)
            if search_term:
                filtered = [row for row in filtered if search_term in row['partner'].casefold()]
            return {
                'title': title,
                'total': global_total,
                'count': len(positive_rows),
                'filtered_count': len(filtered),
                'filter': filter_key or 'all',
                'rows': filtered[:4],
                'action': open_model(
                    f"Liste exhaustive - {title}",
                    'account.move.line',
                    balance_domain,
                    {'group_by': ['partner_id']},
                    'list,pivot,graph',
                ),
            }

        kpi_definitions = {
            'customers': ('Top créances client', 1, 'customer_receivable_filter'),
            'suppliers': ('Top créances fournisseur', -1, 'supplier_receivable_filter'),
        }
        requested_types = [search_type] if search_type in kpi_definitions else list(kpi_definitions)
        return {
            kpi_type: build_kpi(
                kpi_definitions[kpi_type][0],
                kpi_definitions[kpi_type][1],
                kpi_filters.get(kpi_definitions[kpi_type][2], 'all'),
                kpi_type,
            )
            for kpi_type in requested_types
        }

    def get_partner_balance_kpis(self, filters=None):
        """Return the independently searchable partner KPIs without reloading the board."""
        def open_model(name, model, domain=None, context=None, views=None):
            view_mode = views or 'list,form'
            return {
                'type': 'ir.actions.act_window',
                'name': name,
                'res_model': model,
                'view_mode': view_mode,
                'views': [[False, mode] for mode in view_mode.split(',')],
                'domain': domain or [],
                'context': context or {},
            }

        return self._get_partner_balance_kpis(open_model, filters)

    def _get_partner_balance_extra_account_ids(self):
        account_ids = set()
        Journal = self.env['account.journal']
        journal_account_fields = [
            'suspense_account_id',
            'payment_debit_account_id',
            'payment_credit_account_id',
            'outstanding_receipts_account_id',
            'outstanding_payments_account_id',
        ]
        for journal in Journal.search([]):
            for field_name in journal_account_fields:
                if field_name in Journal._fields:
                    account = journal[field_name]
                    if account:
                        account_ids.add(account.id)
        return list(account_ids)

    @api.model
    def get_dashboard_kpis(self, filters=None):
        filters = filters or {}
        today = date.today()
        current_month_start = today.replace(day=1)
        previous_month_start = current_month_start - relativedelta(months=1)
        sales = sum(self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]).mapped('amount_untaxed'))
        purchases = sum(self.env['purchase.order'].search([('state', 'in', ['purchase', 'done'])]).mapped('amount_untaxed'))
        gross_margin = sales - purchases
        cash_balance = sum(self.env['account.account'].search([('account_type', '=', 'asset_cash')]).mapped('current_balance'))
        current_revenue = sum(self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', current_month_start)]).mapped('amount_total')) + self._sum_pos_orders([('date_order', '>=', current_month_start)])
        previous_revenue = sum(self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', previous_month_start), ('invoice_date', '<', current_month_start)]).mapped('amount_total')) + self._sum_pos_orders([('date_order', '>=', previous_month_start), ('date_order', '<', current_month_start)])
        revenue_trend = (current_revenue - previous_revenue) / previous_revenue * 100 if previous_revenue else 100
        current_purchases = sum(self.env['purchase.order'].search([('state', 'in', ['purchase', 'done']), ('date_approve', '>=', current_month_start)]).mapped('amount_total'))
        previous_purchases = sum(self.env['purchase.order'].search([('state', 'in', ['purchase', 'done']), ('date_approve', '>=', previous_month_start), ('date_approve', '<', current_month_start)]).mapped('amount_total'))
        purchases_trend = (current_purchases - previous_purchases) / previous_purchases * 100 if previous_purchases else 100
        customer_receivables = sum(self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial'])]).mapped('amount_residual'))
        deliveries_pending = self.env['stock.picking'].search_count([('picking_type_code', '=', 'outgoing'), ('state', 'not in', ['done', 'cancel'])])
        return {'cash_balance': cash_balance, 'gross_margin': gross_margin, 'revenue': current_revenue, 'revenue_trend': round(revenue_trend, 1), 'purchases': current_purchases, 'purchases_trend': round(purchases_trend, 1), 'receivables': customer_receivables, 'receivables_trend': 0, 'deliveries': deliveries_pending, 'deliveries_trend': 0}

    @api.model
    def get_top_unpaid_invoices(self, filters=None):
        domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial'])]
        domain += self._get_date_domain(filters, 'invoice_date')
        invoices = self.env['account.move'].search(domain)
        customers = {}
        for invoice in invoices:
            partner = invoice.partner_id
            if partner.id not in customers:
                customers[partner.id] = {'id': partner.id, 'customer': partner.name, 'residual': 0, 'invoice_count': 0}
            customers[partner.id]['residual'] += invoice.amount_residual
            customers[partner.id]['invoice_count'] += 1
        result = sorted(customers.values(), key=lambda x: x['residual'], reverse=True)
        return result

    @api.model
    def get_top_reserved_products(self, filters=None):
        domain = [('picking_id.picking_type_code', '=', 'outgoing'), ('picking_id.state', 'not in', ['done', 'cancel'])]
        moves = self.env['stock.move'].search(domain)
        products = {}
        for move in moves:
            product = move.product_id
            customer = move.picking_id.partner_id.name or '-'
            if product.id not in products:
                products[product.id] = {'id': product.id, 'name': product.display_name, 'qty': 0, 'delivery_count': 0, 'customers': set(), 'picking_ids': set(), 'pickings': set()}
            products[product.id]['qty'] += move.product_uom_qty
            products[product.id]['delivery_count'] += 1
            products[product.id]['customers'].add(customer)
            products[product.id]['picking_ids'].add(move.picking_id.id)
            products[product.id]['pickings'].add(move.picking_id.name)
        for product in products.values():
            product['customer'] = ', '.join(list(product['customers'])[:3])
            product['picking_ids'] = list(product['picking_ids'])
            product['pickings'] = ', '.join(list(product['pickings'])[:3])
            del product['customers']
        result = sorted(products.values(), key=lambda x: x['qty'], reverse=True)
        return result

    @api.model
    def get_revenue_chart(self, filters=None):
        from collections import defaultdict
        from datetime import date
        filters = filters or {}
        period = filters.get('period', 'year')
        domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]
        domain += self._get_date_domain(filters, 'invoice_date')
        invoices = self.env['account.move'].search(domain)
        revenue_chart = defaultdict(float)
        receivable_chart = defaultdict(float)
        if period == 'year':
            labels = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
            for invoice in invoices:
                if not invoice.invoice_date:
                    continue
                month_index = invoice.invoice_date.month - 1
                revenue_chart[month_index] += invoice.amount_untaxed
                if invoice.payment_state in ['not_paid', 'partial']:
                    receivable_chart[month_index] += invoice.amount_residual
            revenue_values = [revenue_chart[i] for i in range(12)]
            receivable_values = [receivable_chart[i] for i in range(12)]
        else:
            today = date.today()
            labels = [str(day) for day in range(1, today.day + 1)]
            revenue_values = [0 for _ in labels]
            receivable_values = [0 for _ in labels]
            for invoice in invoices:
                if not invoice.invoice_date:
                    continue
                if invoice.invoice_date.month != today.month or invoice.invoice_date.year != today.year:
                    continue
                idx = invoice.invoice_date.day - 1
                revenue_values[idx] += invoice.amount_untaxed
                if invoice.payment_state in ['not_paid', 'partial']:
                    receivable_values[idx] += invoice.amount_residual
        if 'pos.order' in self.env.registry:
            pos_orders = self.env['pos.order'].search(self._get_date_domain(filters, 'date_order'))
            for order in pos_orders:
                if not order.date_order:
                    continue
                if period == 'year':
                    revenue_values[order.date_order.month - 1] += order.amount_total
                elif order.date_order.month == today.month and order.date_order.year == today.year:
                    idx = order.date_order.day - 1
                    if 0 <= idx < len(revenue_values):
                        revenue_values[idx] += order.amount_total
        return {'labels': labels, 'revenue': revenue_values, 'receivables': receivable_values, 'total_revenue': sum(revenue_values), 'total_receivables': sum(receivable_values)}

    @api.model
    def get_activity_chart(self):
        revenue = sum(self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]).mapped('amount_untaxed'))
        purchases = sum(self.env['purchase.order'].search([('state', 'in', ['purchase', 'done'])]).mapped('amount_untaxed'))
        receivables = sum(self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial'])]).mapped('amount_residual'))
        reserved_stock = self.env['stock.move'].search_count([('picking_id.picking_type_code', '=', 'outgoing'), ('state', 'in', ['assigned', 'partially_available'])])
        return {'labels': ['CA', 'Achats', 'Créances', 'Réservations'], 'values': [revenue, purchases, receivables, reserved_stock]}

    def _get_date_domain(self, filters, field_name):
        filters = filters or {}
        period = filters.get('period', 'month')
        today = date.today()
        if period == 'today':
            return [(field_name, '>=', today), (field_name, '<=', today)]
        if period == 'week':
            start = today - timedelta(days=today.weekday())
            return [(field_name, '>=', start)]
        if period == 'month':
            start = today.replace(day=1)
            return [(field_name, '>=', start)]
        if period == 'year':
            start = today.replace(month=1, day=1)
            return [(field_name, '>=', start)]
        if period == 'custom':
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            domain = []
            if date_from:
                domain.append((field_name, '>=', date_from))
            if date_to:
                domain.append((field_name, '<=', date_to))
            return domain
        return []

    @api.model
    def get_alerts(self):
        alerts = []
        invoices = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial'])])
        partners = {}
        for invoice in invoices:
            partner = invoice.partner_id
            if partner.id not in partners:
                partners[partner.id] = {'id': partner.id, 'name': partner.name, 'amount': 0}
            partners[partner.id]['amount'] += invoice.amount_residual
        critical_clients = [p for p in partners.values() if p['amount'] >= 5000000]
        if critical_clients:
            alerts.append({'type': 'danger', 'title': 'Créances Critiques', 'count': len(critical_clients), 'amount': sum((x['amount'] for x in critical_clients)), 'items': sorted(critical_clients, key=lambda x: x['amount'], reverse=True)[:10]})
        overdue_items = []
        overdue_invoices = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial']), ('invoice_date_due', '<', fields.Date.today())])
        for invoice in overdue_invoices:
            delay = (fields.Date.today() - invoice.invoice_date_due).days
            if delay > 60:
                level = 'critical'
            elif delay > 30:
                level = 'warning'
            else:
                level = 'normal'
            overdue_items.append({'id': invoice.id, 'name': invoice.name, 'customer': invoice.partner_id.name, 'amount': invoice.amount_residual, 'delay': delay, 'level': level})
        if overdue_items:
            alerts.append({'type': 'warning', 'title': 'Factures en Retard', 'count': len(overdue_items), 'items': overdue_items[:10]})
        blocked_items = []
        pickings = self.env['stock.picking'].search([('picking_type_code', '=', 'outgoing'), ('state', 'not in', ['done', 'cancel'])])
        today = fields.Date.today()
        for picking in pickings:
            if picking.scheduled_date:
                delay = (today - picking.scheduled_date.date()).days
                if delay >= 7:
                    blocked_items.append({'id': picking.id, 'name': picking.name, 'amount': delay})
        if blocked_items:
            alerts.append({'type': 'warning', 'title': 'Livraisons Bloquées', 'count': len(blocked_items), 'items': blocked_items[:10]})
        low_stock_items = []
        min_qty = self.env['primetech.reporting.settings'].get_values()['stock_min_alert_threshold']
        warning_qty = max(min_qty / 2.0, 1.0)
        products = self.env['product.product'].search([('active', '=', True), ('sale_ok', '=', True)])
        for product in products:
            qty = int(product.qty_available)
            if qty < min_qty:
                if qty <= 0:
                    level = 'critical'
                elif qty < warning_qty:
                    level = 'warning'
                else:
                    level = 'low'
                low_stock_items.append({'id': product.id, 'name': product.display_name, 'qty': qty, 'sale_price': product.lst_price, 'level': level, 'model': 'product.product'})
        low_stock_items = sorted(low_stock_items, key=lambda item: item['qty'])
        if low_stock_items:
            alerts.append({'type': 'low_stock', 'title': '⚠ Stock Faible', 'count': len(low_stock_items), 'items': low_stock_items})
        return alerts

    @api.model
    def get_receivables_chart(self, filters=None):
        current_year = fields.Date.today().year
        result = {}
        for month in range(1, 13):
            invoices = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial']), ('invoice_date', '>=', date(current_year, month, 1)), ('invoice_date', '<=', date(current_year, month, monthrange(current_year, month)[1]))])
            result[month] = sum(invoices.mapped('amount_residual'))
        return {'labels': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'], 'values': [result.get(i, 0) for i in range(1, 13)]}
