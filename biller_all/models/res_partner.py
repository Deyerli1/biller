# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

ID_TYPE = {
    'rut' : "general_regimen",
    'ci' : "end_consumer",
    'others' : False,
    'passport' : "foreign_partner",
    'nin' : False,
    'nife' : False
    }
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
    
    @api.constrains('fiscal_document_type')
    def check_fiscal_document_type(self):
        for record in self:
            fiscal_position = record.property_account_position_id
            if fiscal_position and fiscal_position.type != ID_TYPE[record.fiscal_document_type]:
                raise ValidationError("El documento del tipo {} no coincide con la posicion fiscal {}".format(record.fiscal_document_type, fiscal_position.name))
                
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
