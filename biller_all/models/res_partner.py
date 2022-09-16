# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    fiscal_document_type = fields.Selection([
        ('rut', 'RUT'),
        ('ci', 'CI'),
        ('others', 'Otros'),
        ('passport', 'Pasaporte'),
        ('nin', 'DNI'),
        ('nife', 'NIFE'),], 
        required=True,
        string = "Tipo de Documento"
    )

    foreign_contact = fields.Boolean("Cliente del exterior")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
