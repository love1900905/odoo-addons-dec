# -*- encoding: utf-8 -*-

import time

from openerp import models, fields, api


class res_partner(models.Model):

    _inherit="res.partner"
    _columns = {
        'partner_academy': fields.many2one('res.partner.academy', 'Academy', help="Educational academy of the current partner."),
        'zip': fields.related('address', 'zip', type='char', string='Zip'),
    }
    
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        res = super(res_partner,self).name_search(cr, uid, name=name, args=args, operator=operator, context=context, limit=limit)

        result = []
        for item in res:
            item = list(item)
            data = self.read(cr, uid, item[0], ['city', 'zip'], context=context)
            if data['zip'] and data['city']:
                item[1] = ('%s (%s %s)') % (item[1], data['zip'], data['city'])
            result.append(item)
            
        return result

res_partner()