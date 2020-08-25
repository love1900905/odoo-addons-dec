# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Mar 2020

import time
import logging


from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.addons.tools_miscellaneous.tools.bench import Bench

_logger = logging.getLogger(__name__)


class RefReference(models.Model):
    """ Description """

    _name = 'ref.reference'
    _description = 'Reference'
    _rec_name = 'value'
    _order = 'value'

    category_id = fields.Many2one(
        'ref.category',
        'Category',
        required=True,
        oldname='category',
    )
    product_id = fields.Many2one(
        'product.template',
        'Product',
        required=True,
        oldname='product',
    )
    public_code = fields.Char(
        related='product_id.public_code',
        string='Public Code',
        oldname='product_ciel_code',
    )
    name = fields.Char(
        related='product_id.name',
        string='Name',
        oldname='product_name',
    )
    state = fields.Selection(
        related='product_id.state',
        string='Status',
        oldname='product_state',
    )
    internal_notes = fields.Text(
        related='product_id.internal_notes',
        string='Internal Notes',
        oldname='product_comments',
    )
    current_version = fields.Integer(
        'Current version',
        required=True,
    )
    value = fields.Text(
        'Value',
        required=True,
    )
    searchvalue = fields.Text(
        'Search value',
        required=True,
    )
    datetime = fields.Datetime(
        'Create date', required=True, default=fields.Datetime.now
    )
    folder_count = fields.Integer('Product folder item count')
    folder_error = fields.Integer('Product folder error count')
    folder_warning = fields.Integer('Product folder warning count')
    folder_task = fields.Integer('Product folder task count')
    picturepath = fields.Text('Path to picture')

    reference_line_ids = fields.One2many(
        'ref.reference.line',
        'reference_id',
        string='Lines',
        oldname='reference_lines',
    )
    version_ids = fields.One2many(
        'ref.version',
        'reference_id',
        string='Versions',
        oldname='version_lines',
    )

    _sql_constraints = [
        ('value_uniq', 'unique(value)', 'Reference value must be unique !'),
    ]

    @api.model
    def create(self, values):
        product_id = values.get('product_id')
        if product_id:
            product = self.env['product.product'].browse(product_id)
            product.mrp_production_request = True
        reference = super().create(values)
        return reference

    @api.model
    def search_custom(self, keywords):
        res = []
        bench = Bench().start()
        for key in keywords[0]:
            if key and key[0] == '+':
                use_internal_notes = True
                key = key[1:]
            else:
                use_internal_notes = False

            if key:
                res_value = self.search([
                    ('searchvalue', 'ilike', key),
                ])
                res += res_value.ids
                res_category = self.search(
                    [
                        ('category_id.name', 'ilike', key),
                    ]
                )
                res += res_category.ids
                res_name = self.search([
                    ('product_id.name', 'ilike', key),
                ])
                res += res_name.ids
                res_public_code = self.search(
                    [
                        ('product_id.public_code', '=', key),
                    ]
                )
                res += res_public_code.ids

                if use_internal_notes:
                    res_internal_notes = self.search(
                        [
                            ('product_id.internal_notes', 'ilike', key),
                        ]
                    )
                    res += res_internal_notes.ids
                # A tag must be at least 2 characters
                if len(key) > 2:
                    res_tags = self.search(
                        [
                            ('product_id.tagging_ids.name', 'ilike', key),
                        ]
                    )
                    res += res_tags.ids

        _logger.info('Search elapsed time is %s', bench.stop().duration())
        return res
