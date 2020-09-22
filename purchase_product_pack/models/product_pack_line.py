# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Sep 2020

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class ProductPackLine(models.Model):
    _inherit = 'product.pack.line'

    @api.multi
    def get_purchase_order_line_vals(self, line, order):
        self.ensure_one()
        quantity = self.quantity * line.product_uom_qty
        line_vals = {
            'order_id': order.id,
            'product_id': self.product_id.id or False,
            'pack_parent_line_id': line.id,
            'pack_depth': line.pack_depth + 1,
            'company_id': order.company_id.id,
            'pack_modifiable': line.product_id.pack_modifiable,
        }
        if line.move_dest_ids:
            line_move = line.move_dest_ids[0]
            move = {
                "name":
                    '%s%s' % (
                        '> ' *
                        (line.pack_depth + 1), self.product_id.display_name
                    ),
                "reference":
                    line_move.reference,
                "procure_method":
                    line_move.procure_method,
                "location_id":
                    line_move.location_id.id,
                "location_dest_id":
                    line_move.location_dest_id.id,
                "product_id":
                    self.product_id.id,
                "product_uom":
                    self.product_id.uom_id.id,
                "product_uom_qty":
                    quantity,
                "origin":
                    line_move.origin,
                "group_id":
                    line_move.group_id.id,
                "created_purchase_line_id":
                    False,
                "raw_material_production_id":
                    line_move.raw_material_production_id.id,
                "auto_validate":
                    line_move.auto_validate,
                "move_dest_ids": [(6, 0, line_move.move_dest_ids.ids)],
            }
            line_vals['move_dest_ids'] = [(0, 0, move)]
        sol = line.new(line_vals)
        sol.move_dest_ids._recompute_state()
        sol.onchange_product_id()
        sol.product_uom_qty = quantity
        sol._onchange_quantity()
        vals = sol._convert_to_write(sol._cache)
        pack_price_types = {'totalized', 'ignored'}
        if (
            line.product_id.pack_type == 'detailed' and
            line.product_id.pack_component_price in pack_price_types
        ):
            vals['price_unit'] = 0.0
        vals.update(
            {
                'name': '%s%s' % ('> ' * (line.pack_depth + 1), sol.name),
            }
        )
        return vals
