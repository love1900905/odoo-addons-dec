# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, May 2020

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    supply_method = fields.Char(
        compute='_compute_supply_method',
        inverse='_inverse_supply_method',
        string='Supply method',
        help=
        "Produce will generate production order or tasks, according to the \
product type. Buy will trigger purchase orders when requested.",
    )

    procure_method = fields.Char(
        compute='_compute_procure_method',
        inverse='_inverse_procure_method',
        string='Procurement method',
        help=
        "'Make to Stock': When needed, take from the stock or wait until \
re-supplying. 'Make to Order': When needed, purchase or produce for the \
procurement request.",
    )

    @api.model
    def _get_buy_route(self):
        # buy: purchase_stock.route_warehouse0_buy -> _get_buy_route
        buy_route = self.env['stock.warehouse']._find_global_route(
            'purchase_stock.route_warehouse0_buy',
            _('Buy'),
        )
        return buy_route

    @api.model
    def _get_produce_route(self):
        # buy: purchase_stock.route_warehouse0_buy -> _get_buy_route
        produce_route = self.env['stock.warehouse']._find_global_route(
            'mrp.route_warehouse0_manufacture',
            _('Manufacture'),
        )
        return produce_route

    @api.model
    def _get_mto_route(self):
        # make_to_order: stock.route_warehouse0_mto
        mto_route = self.env['stock.warehouse']._find_global_route(
            'stock.route_warehouse0_mto',
            _('Make To Order'),
        )
        return mto_route

    @api.multi
    @api.depends('route_ids')
    def _compute_supply_method(self):
        buy_route = self._get_buy_route()
        produce_route = self._get_produce_route()
        for product in self:
            if produce_route in product.route_ids and \
                not buy_route in product.route_ids:
                product.supply_method = 'produce'
            elif buy_route in product.route_ids and \
                not produce_route in product.route_ids:
                product.supply_method = 'buy'

    @api.multi
    def _inverse_supply_method(self):
        buy_route = self._get_buy_route()
        produce_route = self._get_produce_route()
        for product in self:
            if product.supply_method == 'produce':
                product.route_ids += produce_route
                product.route_ids -= buy_route
            elif product.supply_method == 'buy':
                product.route_ids += buy_route
                product.route_ids -= produce_route

    @api.multi
    @api.depends('route_ids')
    def _compute_procure_method(self):
        mto_route = self._get_mto_route()
        for product in self:
            if mto_route in product.route_ids:
                product.procure_method = 'make_to_order'
            else:
                product.procure_method = 'make_to_stock'

    @api.multi
    def _inverse_procure_method(self):
        mto_route = self._get_mto_route()
        for product in self:
            if product.procure_method == 'make_to_order':
                product.route_ids += mto_route
            elif product.procure_method == 'make_to_stock':
                product.route_ids -= mto_route
