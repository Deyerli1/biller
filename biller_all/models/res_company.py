# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class Company(models.Model):
    _inherit = 'res.company'

    access_token = fields.Char("Token de acceso Biller")
    
    branch_office = fields.Integer("Sucursal ID Biller")

#@api.onchange("access_token")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
