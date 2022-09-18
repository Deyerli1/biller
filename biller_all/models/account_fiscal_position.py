# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    type = fields.Selection([
        ('general_regimen', 'Regimen General'),
        ('end_consumer', 'Consumidor Final'),
        ('foreign_partner', 'Contacto del Exterior'),], 
        string = "Tipo"
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
