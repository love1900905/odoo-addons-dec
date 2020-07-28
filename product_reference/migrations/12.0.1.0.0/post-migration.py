# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Mar 2020

import logging

from openupgradelib import openupgrade
_logger = logging.getLogger(__name__)

columns = [
    'ciel_code',
    'comments',
    'market_bom_id',
    'market_markup_rate',
    'market_material_cost_factor',
    'public_code',
    'internal_notes',
]

PRODUCT = 'product_product'


@openupgrade.progress()
def migrate_product_state(env, version):
    for ref in env['ref.reference'].search([('state', '=', False)]):
        if ref.product_id.state == False:
            _logger.info(
                '{}: {}'.format(ref.product_id.name, ref.product_id.state)
            )
            ref.product_id.state = 'quotation'

    openupgrade.logged_query(
        env.cr, """
        UPDATE product_template SET state='normal'
        WHERE state is NULL;
        """
    )


@openupgrade.migrate()
def migrate(env, version):
    legacy_mapping = [(x, openupgrade.get_legacy_name(x)) for x in columns]

    mapping_str = []
    for item in legacy_mapping:
        if openupgrade.column_exists(env.cr, PRODUCT, item[1]):
            new_col_name = item[0]
            # Force new names since framework will create column with these
            # names.
            if new_col_name == 'ciel_code':
                new_col_name = 'public_code'
            if new_col_name == 'comments':
                new_col_name = 'internal_notes'

            mapping_str.append('{0}=pp.{1}'.format(new_col_name, item[1]))

    if mapping_str:
        print(legacy_mapping)
        openupgrade.logged_query(
            env.cr, """
            UPDATE product_template pt SET
                {0}
            FROM product_product pp
            WHERE pt.id = pp.id
            """.format(','.join(mapping_str))
        )

        # Remove old columns
        for item in legacy_mapping:
            if openupgrade.column_exists(env.cr, PRODUCT, item[1]):
                openupgrade.drop_columns(env.cr, [
                    (PRODUCT, item[1]),
                ])

    migrate_product_state(env, version)