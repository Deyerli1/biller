# -*- encoding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import json

ID_TYPE = {
    'rut' : [2, 0],
    'ci' : [3, -10],
    'others' : [4],
    'passport' : [5, 10],
    'nin' : 6,
    'nife' : 7
}

CODES = {
    'out_invoice' : 111,
    'in_invoice' : 111,
    'out_refund' : 112,
    'in_refund' : 113,
}

class AccountMove(models.Model):
    _inherit = 'account.move'

    biller_id = fields.Integer("ID Biller",readonly=True,copy=False)

    associated_move_ids = fields.Many2one(
        comodel_name = 'account.move',
        string = "CFEs asociadas",
        copy=False,
    )

    def _post(self, soft=True):
        if self.move_type in ('out_invoice','out_refund'):
            self.validate_fields()
            biller_proxy = self.env['biller.record']
            payload = json.dumps(self.get_payload())
            response, data = biller_proxy.post_document(payload,'cfe_sent')
            if response.code != 201:
                raise ValidationError("Hubo problemas al enviar la factura")
            else:
                self.update({
                    'name' : eval(data.decode())["serie"] + "-" + str(eval(data.decode())["numero"]),
                    'biller_id' : eval(data.decode())["id"]
                })
        res = super()._post(soft)
        return res

    def get_payload(self):
        doc_type_offset = ID_TYPE[self.partner_id.fiscal_document_type][1]
        document_type = CODES[self.move_type] + doc_type_offset
        exchange_rate = self.currency_id.rate_ids.filtered(lambda r: r.company_id == self.company_id).rate if self.currency_id.name != 'UYU' else 1
        payload = ({
            "tipo_comprobante": document_type,
            "forma_pago": 2,
            "fecha_emision" : self.invoice_date.strftime("%d/%m/%Y"),
            "fecha_vencimiento" :self.invoice_date_due.strftime("%d/%m/%Y"),
            "sucursal": self.company_id.branch_office,
            "moneda": self.currency_id.name,
            "tasa_cambio" : exchange_rate,
            "montos_brutos": 0,
            "cliente": {
                "tipo_documento": ID_TYPE[self.partner_id.fiscal_document_type][0],
                "documento": self.partner_id.vat,
                "razon_social": self.partner_id.name[:150],
            "sucursal": {
                "direccion": self.partner_id.street[:70] if self.partner_id.street else '',
                "ciudad": self.partner_id.city[:30] if self.partner_id.city else '',
                "departamento": self.partner_id.state_id.name[:30] if self.partner_id.state_id.name else '',
                "pais": self.partner_id.country_id.code
                }
            },
            'items' : self.get_items(),
            'descuentosRecargos': self.get_discounts(),
            'referencias' : self.get_references()
            })
        return payload

    def validate_fields(self):
        if not self.invoice_date:
            raise ValidationError("Es necesario ingresar fecha de emision")
        if not self.partner_id.fiscal_document_type:
            raise ValidationError("El cliente debe tener asignada posicion fiscal")
        if not self.partner_id.country_id.code:
            raise ValidationError("El cliente debe tener asignado un pais")

        return
    
    def get_items(self):
        items=[]
        for line in self.invoice_line_ids.filtered(lambda l: not l.product_id.is_discount):
            line_vals = {
                "cantidad": line.quantity,
                "concepto": line.name[:80],
                "codigo_ean" : int(line.product_id.barcode),
                "precio": line.price_unit,
                "indicador_facturacion": line.invoicing_indicator,
                "descuento_tipo": "%",
                "descuento_cantidad": line.discount,          
            }
            items.append(line_vals)
        return items

    def get_discounts(self):
        discounts=[]
        for line in self.invoice_line_ids.filtered(lambda l: l.product_id.is_discount):
            discount_vals = {
                'es_recargo' : True if line.price_unit > 0 else False,
                "glosa" : line.name[:50],
                "desc_rec_tipo": '$',
                "valor": abs(line.price_unit),
                "indicador_facturacion": line.invoicing_indicator,
            }
            discounts.append(discount_vals)
        return discounts
    
    def get_references(self):
        references=[]
        if self.reversed_entry_id:
            references.append(self.reversed_entry_id.biller_id)
        return references

    def print_biller_pdf(self):
        for record in self:
            if record.state != 'posted':
                raise ValidationError("La factura {} no se encuentra publicada en Biller".format(record.name))
            wizard_proxy = record.env['download.pdf.wizard']
            return wizard_proxy.print_biller_pdf(record.biller_id, record.name, record.company_id.access_token)        
     
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
