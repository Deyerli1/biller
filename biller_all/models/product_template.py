# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_discount = fields.Boolean("Es descuento o recargo")

    discount_overcharge = fields.Selection([
            ('discount', 'Descuento'), 
            ('overcharge', 'Recargo')],
            string = "Recargo/Descuento"
            )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
