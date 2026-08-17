# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class StockDashboardController(http.Controller):

    @http.route('/primetech/stock/dashboard', type='json', auth='user')
    def get_dashboard_data(self, period='month'):
        return request.env['pt.stock.dashboard'].sudo().get_dashboard_data({'period': period})
