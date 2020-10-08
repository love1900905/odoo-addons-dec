{
    'name': 'Sale Purchase Traceability',
    'version': '12.0.1.0.0',
    'author': 'DEC, Yann Papouin',
    'website': 'http://www.dec-industrie.com',
    'category': 'Sales',
    'summary': '''Show related purchases on sale order line form''',
    'depends': [
        'sale_traceability',
        'sale_row_layout',
        'sale_purchase',
    ],
    #'force_migration':'12.0.0.0.0',
    'data':
        [
            'security/res_groups.xml',
            'views/sale_order.xml',
        ],
    'installable': True
}
