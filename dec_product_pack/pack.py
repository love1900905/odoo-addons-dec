# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2009 Angel Avarez - NaN  (http://www.nan-tic.com) All Rights Reserved.
#
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import math
from osv import fields,osv

class product_pack_sale( osv.osv ):
    _name = 'product.pack.saleline'
    _rec_name = 'product_id'
    _columns = {
        'parent_product_id': fields.many2one('product.product', 'Parent Product', ondelete='cascade', required=True),
        'quantity': fields.float('Quantity', required=True ),
        'product_id': fields.many2one('product.product', 'Product', required=True ),
        'product_name': fields.related('product_id', 'name', type='char', string='Name'),
        'product_code': fields.related('product_id', 'default_code', type='char', string='Default code'),        
        'product_uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string="Default Unit Of Measure", readonly="1"),
        'product_categ_id': fields.related('product_id', 'categ_id', type='many2one', relation='product.category', string="Category"),
    }
    
    _defaults = {
        'quantity': 1.0,
    }

product_pack_sale()

class product_pack_purchase( osv.osv ):
    _name = 'product.pack.purchaseline'
    _rec_name = 'product_id'
    _columns = {
        'parent_product_id': fields.many2one('product.product', 'Parent Product', ondelete='cascade', required=True),
        'quantity': fields.float('Quantity', required=True ),
        'product_id': fields.many2one('product.product', 'Product', required=True ),   
        'product_name': fields.related('product_id', 'name', type='char', string='Name'),
        'product_code': fields.related('product_id', 'default_code', type='char', string='Default code'),
        'product_uom_id': fields.related('product_id', 'uom_po_id', type='many2one', relation='product.uom', string="Purchase Unit of Measure", readonly="1"),
        'product_categ_id': fields.related('product_id', 'categ_id', type='many2one', relation='product.category', string="Category"),
    }
    
    _defaults = {
        'quantity': 1.0,
    }

product_pack_purchase()

class product_product( osv.osv ):
    _inherit = 'product.product'
    _columns = {
        'stock_depends': fields.boolean( 'Stock depends of components', help='Mark if pack stock is calculated from component stock' ),       
        'sale_pack_line_ids': fields.one2many('product.pack.saleline','parent_product_id', 'Pack Products', help='List of products that are part of this pack.' ),
        'fixed_sale_price': fields.boolean('Pack has fixed price', help='Mark this field if the price of the pack should be fixed. Do not mark it if the price should be calculated from the sum of the prices of the products in the pack.' ),
        'purchase_pack_line_ids': fields.one2many('product.pack.purchaseline','parent_product_id', 'Pack Products', help='List of products that are part of this pack.' ),
        'fixed_purchase_price': fields.boolean('Pack has fixed price', help='Mark this field if the price of the pack should be fixed. Do not mark it if the price should be calculated from the sum of the prices of the products in the pack.' ),
    }   
    
    _defaults = {
        'fixed_sale_price': True,
        'fixed_purchase_price': True,
    }

    def get_product_available( self, cr, uid, ids, context=None ):
        """ Calulate stock for packs, return  maximum stock that lets complete pack """
        result={}
        for product in self.browse( cr, uid, ids, context=context ):
            stock = super( product_product, self ).get_product_available( cr, uid, [ product.id ], context=context )

            # Check if product stock depends on it's subproducts stock.
            if not product.stock_depends:
                result[ product.id ] = stock[ product.id ]
                continue

            first_subproduct = True
            pack_stock = 0
            
            pack_line_ids = None
            if product.sale_pack_line_ids:
                pack_line_ids = product.sale_pack_line_ids
            else:
                if product.purchase_pack_line_ids:
                    pack_line_ids = product.purchase_pack_line_ids
                  

            # Check if the pack has subproducts
            if pack_line_ids:
                # Take the stock/virtual stock of all subproducts
                subproducts_stock = self.get_product_available( cr, uid, [ line.product_id.id for line in pack_line_ids ], context=context )
                # Go over all subproducts, take quantity needed for the pack and its available stock
                for subproduct in pack_line_ids:
                    if first_subproduct:
                        subproduct_quantity = subproduct.quantity
                        subproduct_stock = subproducts_stock[ subproduct.product_id.id ]
                        # Calculate real stock for current pack from the subproduct stock and needed quantity
                        pack_stock = math.floor( subproduct_stock / subproduct_quantity )
                        first_subproduct = False
                        continue
                    # Take the info of the next subproduct
                    subproduct_quantity_next = subproduct.quantity
                    subproduct_stock_next = subproducts_stock[ subproduct.product_id.id ]
                    pack_stock_next = math.floor( subproduct_stock_next / subproduct_quantity_next )
                    # compare the stock of a subproduct and the next subproduct
                    if pack_stock_next < pack_stock:
                        pack_stock = pack_stock_next
                # result is the minimum stock of all subproducts
                result[ product.id ] = pack_stock
            else:
                result[ product.id ] = stock[ product.id ]
        return result

product_product()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'pack_depth': fields.integer('Depth', required=True, help='Depth of the product if it is part of a pack.'),
        'pack_parent_line_id': fields.many2one('sale.order.line', 'Pack', help='The pack that contains this product.'),
        'pack_child_line_ids': fields.one2many('sale.order.line', 'pack_parent_line_id', 'Lines in pack', help=''),
        'pack_expand': fields.boolean( 'Pack expand', help='If checked, the product pack will be automatically expanded when computed' ),
    }
    _defaults = {
        'pack_depth': lambda *a: 0,
        'pack_expand': True,
    }
    
    def create(self, cr, user, vals, context=None):
        result = super(sale_order_line, self).create(cr, user, vals, context) 
        return result
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
			
        new_line_data = self.read(cr, uid, id, [], context=context)
        original_order_line = self.browse(cr, uid, id, context)
        original_order = self.pool.get('sale.order').browse(cr, uid, original_order_line.order_id.id) 
        
        parent_sequence = -1
        for line in original_order.order_line:
            if line.sequence == line['sequence'] and line.pack_parent_line_id:
                parent_sequence = line.pack_parent_line_id.sequence 
                
        if parent_sequence >= 0:
           parent_sequence = 1000 

		#'product_id': new_line_data['product_id'],
        default.update({'the_test':'YEAAAHHHHH', 'pack_parent_line_id':False, 'pack_child_line_ids':False, 'pack_depth':0})
        result = super(sale_order_line, self).copy_data(cr, uid, id, default, context=context) 
        return result
    
sale_order_line()

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def create(self, cr, uid, vals, context=None):
        result = super(sale_order,self).create(cr, uid, vals, context)
        #self.expand_packs(cr, uid, [result], context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        result = super(sale_order,self).write(cr, uid, ids, vals, context)
        self.expand_packs(cr, uid, ids, context)
        return result
    
    def copy(self, cr, uid, ids, vals, context=None):
        result = super(sale_order,self).copy(cr, uid, ids, vals, context)
        return result

    def expand_packs(self, cr, uid, ids, context={}, depth=1):
        if depth == 10:
            return
        updated_orders = []
        for order in self.browse(cr, uid, ids, context):
            
            fiscal_position = order.fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, order.fiscal_position, context) or False

            # The reorder variable is used to ensure lines of the same pack go right after their 
            # parent.
            # What the algorithm does is check if the previous item had children. As children items 
            # must go right after the parent if the line we're evaluating doesn't have a parent it
            # means it's a new item (and probably has the default 10 sequence number - unless the 
            # appropiate c2c_sale_sequence module is installed). In this case we mark the item for
            # reordering and evaluate the next one. Note that as the item is not evaluated and it might
            # have to be expanded it's put on the queue for another iteration (it's simple and works well).
            # Once the next item has been evaluated the sequence of the item marked for reordering is updated
            # with the next value.
            sequence = -1
            reorder = []
            last_had_children = False
            for line in order.order_line:
                if last_had_children and not line.pack_parent_line_id:
                    reorder.append( line.id )
                    if line.product_id.sale_pack_line_ids and not order.id in updated_orders:
                        updated_orders.append( order.id )
                    continue

                sequence += 1

                if sequence > line.sequence:
                    self.pool.get('sale.order.line').write(cr, uid, [line.id], {'sequence': sequence,}, context)
                else:
                    sequence = line.sequence

                if line.state != 'draft':
                    continue
                if not line.product_id:
                    continue

                # If pack was already expanded (in another create/write operation or in 
                # a previous iteration) don't do it again.
                if not line.pack_expand or line.pack_child_line_ids:
                    last_had_children = True
                    continue
                last_had_children = False

                for subline in line.product_id.sale_pack_line_ids:
                    sequence += 1

                    subproduct = subline.product_id
                    quantity = subline.quantity * line.product_uom_qty

                    if line.product_id.fixed_sale_price:
                        price = 0.0
                        discount = 0.0
                    else:
                        pricelist = order.pricelist_id.id
                        price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], 
                                        subproduct.id, quantity, order.partner_id.id, {
                            'uom': subproduct.uom_id.id,
                            'date': order.date_order,
                        })[pricelist]
                        discount = line.discount

                    # Obtain product name in partner's language
                    ctx = {'lang': order.partner_id.lang}
                    subproduct_name = self.pool.get('product.product').browse(cr, uid, subproduct.id, ctx).name

                    tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, fiscal_position, subproduct.taxes_id)

                    if subproduct.uos_id:
                        uos_id = subproduct.uos_id.id
                        uos_qty = quantity * subproduct.uos_coeff
                    else:
                        uos_id = False
                        uos_qty = quantity

                    vals = {
                        'order_id': order.id,
                        'name': '%s %s' % ('>'* (line.pack_depth+1), subproduct_name),
                        'sequence': sequence,
                        'delay': subproduct.sale_delay or 0.0,
                        'product_id': subproduct.id,
                        'procurement_id': line.procurement_id and line.procurement_id.id or False,
                        'price_unit': price,
                        'tax_id': [(6,0,tax_ids)],
                        'type': subproduct.procure_method,
                        'property_ids': [(6,0,[])],
                        'address_allotment_id': False,
                        'product_uom_qty': quantity,
                        'product_uom': subproduct.uom_id.id,
                        'product_uos_qty': uos_qty,
                        'product_uos': uos_id,
                        'product_packaging': False,
                        'move_ids': [(6,0,[])],
                        'discount': discount,
                        'number_packages': False,
                        'notes': False,
                        'th_weight': False,
                        'state': 'draft',
                        'pack_parent_line_id': line.id,
                        'pack_depth': line.pack_depth + 1,
                    }

                    # It's a control for the case that the nan_external_prices was installed with the product pack
                    if 'prices_used' in line:
                        vals[ 'prices_used' ] = line.prices_used

                    self.pool.get('sale.order.line').create(cr, uid, vals, context)
                    if not order.id in updated_orders:
                        updated_orders.append( order.id )

                for id in reorder:
                    sequence += 1
                    self.pool.get('sale.order.line').write(cr, uid, [id], {'sequence': sequence,}, context)

        if updated_orders:
            # Try to expand again all those orders that had a pack in this iteration.
            # This way we support packs inside other packs.
            self.expand_packs(cr, uid, ids, context, depth+1)
        return

sale_order()


class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    _columns = {
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of purchase order lines."),
        'pack_depth': fields.integer('Depth', required=True, help='Depth of the product if it is part of a pack.'),
        'pack_parent_line_id': fields.many2one('purchase.order.line', 'Pack', help='The pack that contains this product.'),
        'pack_child_line_ids': fields.one2many('purchase.order.line', 'pack_parent_line_id', 'Lines in pack', help=''),
        'pack_expand': fields.boolean( 'Pack expand', help='If checked, the product pack will be automatically expanded when computed' ),
    }
    _defaults = {
        'pack_depth': lambda *a: 0,
        'pack_expand': True,
    }
    
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}

        default.update({'pack_parent_line_id':False, 'pack_child_line_ids':False, 'pack_depth':0})
        result = super(purchase_order_line, self).copy_data(cr, uid, id, default, context=context) 
        return result
    
purchase_order_line()


class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    def create(self, cr, uid, vals, context=None):
        result = super(purchase_order,self).create(cr, uid, vals, context)
        self.expand_packs(cr, uid, [result], context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        result = super(purchase_order,self).write(cr, uid, ids, vals, context)
        self.expand_packs(cr, uid, ids, context)
        return result

    def expand_packs(self, cr, uid, ids, context={}, depth=1):
        if depth == 10:
            return
        updated_orders = []
        for order in self.browse(cr, uid, ids, context):
            
            fiscal_position = order.fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, order.fiscal_position, context) or False

            # The reorder variable is used to ensure lines of the same pack go right after their 
            # parent.
            # What the algorithm does is check if the previous item had children. As children items 
            # must go right after the parent if the line we're evaluating doesn't have a parent it
            # means it's a new item (and probably has the default 10 sequence number - unless the 
            # appropiate c2c_sale_sequence module is installed). In this case we mark the item for
            # reordering and evaluate the next one. Note that as the item is not evaluated and it might
            # have to be expanded it's put on the queue for another iteration (it's simple and works well).
            # Once the next item has been evaluated the sequence of the item marked for reordering is updated
            # with the next value.
            sequence = -1
            reorder = []
            last_had_children = False
            for line in order.order_line:
                if last_had_children and not line.pack_parent_line_id:
                    reorder.append( line.id )
                    if line.product_id.purchase_pack_line_ids and not order.id in updated_orders:
                        updated_orders.append( order.id )
                    continue

                sequence += 1

                if sequence > line.sequence:
                    self.pool.get('purchase.order.line').write(cr, uid, [line.id], {
                        'sequence': sequence,
                    }, context)
                else:
                    sequence = line.sequence

                if line.state != 'draft':
                    continue
                if not line.product_id:
                    continue

                # If pack was already expanded (in another create/write operation or in 
                # a previous iteration) don't do it again.
                if not line.pack_expand or line.pack_child_line_ids:
                    last_had_children = True
                    continue
                last_had_children = False

                for subline in line.product_id.purchase_pack_line_ids:
                    sequence += 1

                    subproduct = subline.product_id
                    quantity = subline.quantity * line.product_qty

                    if line.product_id.fixed_purchase_price:
                        price = 0.0
                        discount = 0.0
                    else:
                        pricelist = order.pricelist_id.id
                        price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], subproduct.id, quantity, order.partner_id.id, {
                            'uom': subproduct.uom_id.id,
                            'date': order.date_order,
                        })[pricelist]
                        discount = line.discount

                    # Obtain product name in partner's language
                    ctx = {'lang': order.partner_id.lang}
                    subproduct_name = self.pool.get('product.product').browse(cr, uid, subproduct.id, ctx).name

                    tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, fiscal_position, subproduct.taxes_id)

                    if subproduct.uos_id:
                        uos_id = subproduct.uos_id.id
                        uos_qty = quantity * subproduct.uos_coeff
                    else:
                        uos_id = False
                        uos_qty = quantity

                    vals = {
                        'order_id': order.id,
                        'name': '%s %s' % ('>'* (line.pack_depth+1), subproduct_name),
                        'sequence': sequence,
                        'delay': subproduct.sale_delay or 0.0,
                        'product_id': subproduct.id,
                        #'procurement_id': line.procurement_id and line.procurement_id.id or False,
                        'date_planned': line.date_planned,
                        'price_unit': price,
                        'tax_id': [(6,0,tax_ids)],
                        'type': subproduct.procure_method,
                        'property_ids': [(6,0,[])],
                        'address_allotment_id': False,
                        'product_qty': quantity,
                        'product_uom': subproduct.uom_id.id,
                        'product_uos_qty': uos_qty,
                        'product_uos': uos_id,
                        'product_packaging': False,
                        'move_ids': [(6,0,[])],
                        'discount': discount,
                        'number_packages': False,
                        'notes': False,
                        'th_weight': False,
                        'state': 'draft',
                        'pack_parent_line_id': line.id,
                        'pack_depth': line.pack_depth + 1,
                    }

                    # It's a control for the case that the nan_external_prices was installed with the product pack
                    if 'prices_used' in line:
                        vals[ 'prices_used' ] = line.prices_used

                    self.pool.get('purchase.order.line').create(cr, uid, vals, context)
                    if not order.id in updated_orders:
                        updated_orders.append( order.id )

                for id in reorder:
                    sequence += 1
                    self.pool.get('purchase.order.line').write(cr, uid, [id], {
                        'sequence': sequence,
                    }, context)

        if updated_orders:
            # Try to expand again all those orders that had a pack in this iteration.
            # This way we support packs inside other packs.
            self.expand_packs(cr, uid, ids, context, depth+1)
        return

purchase_order()

