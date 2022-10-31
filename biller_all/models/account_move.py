# -*- encoding: utf-8 -*-
from csv import reader
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

REVERSE_CODES = {
    111 : "in_invoice",
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
        taxes = self.invoice_line_ids.tax_ids.filtered(lambda r: r.price_include == True)
        tax_included = 1 if any(taxes) else 0 
        payload = ({
            "tipo_comprobante": document_type,
            "forma_pago": 1 if self.get_client() == '-' else 2,
            "fecha_emision" : self.invoice_date.strftime("%d/%m/%Y"),
            "fecha_vencimiento" :self.invoice_date_due.strftime("%d/%m/%Y"),
            "sucursal": self.company_id.branch_office,
            "moneda": self.currency_id.name,
            "tasa_cambio" : exchange_rate,
            "montos_brutos": tax_included,
            "cliente": self.get_client(),
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
        for line in self.invoice_line_ids:
            if not line.invoicing_indicator:
                raise ValidationError("Todas las lineas deben tener Indicador de Facturacion")
        return
    
    def get_client(self):
        if self.partner_id.fiscal_document_type == 'ci' and self.partner_id.vat == '-':
           return  "-"
        else:
            return {
                "tipo_documento": ID_TYPE[self.partner_id.fiscal_document_type][0],
                "documento": self.partner_id.vat,
                "razon_social": self.partner_id.name[:150],
                "nombre_fantasia" : self.partner_id.name[:150],
                    "sucursal": {
                        "direccion": self.partner_id.street[:70] if self.partner_id.street else '',
                        "ciudad": self.partner_id.city[:30] if self.partner_id.city else '',
                        "departamento": self.partner_id.state_id.name[:30] if self.partner_id.state_id.name else '',
                        "pais": self.partner_id.country_id.code
                }
            }
    
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
            if self.reversed_entry_id.payment_id:
                self.reversed_entry_id.payment_id.biller_cancel_self()
        return references

    def print_biller_pdf(self):
        for record in self:
            if record.state != 'posted':
                raise ValidationError("La factura {} no se encuentra publicada en Biller".format(record.name))
            wizard_proxy = record.env['download.pdf.wizard']
            return wizard_proxy.print_biller_pdf(record.biller_id, record.name, record.company_id.access_token)   
     
    def create_received(self, vals):
        if self.search([("biller_id", "=", vals["id"])]):
            return
        partner_id = self.get_partner(vals["cliente"])
        
        # Figure out what taxes to apply to the lines
        if vals["tot_iva_tasa_bas"]:
            taxes = self.env['account.tax'].search([('amount', '=', 22), ("type_tax_use", "=", "purchase",)], limit=1).id
        elif vals["tot_iva_tasa_min"]:
            taxes = self.env['account.tax'].search([('amount', '=', 10), ("type_tax_use", "=", "purchase",)], limit=1).id
        else:
            taxes = self.env['account.tax'].search([('amount', '=', 22), ("type_tax_use", "=", "purchase",)], limit=1).id

        # Get lines by looking up the PDF of the document and parsing it
        lines_values_list = self.get_received_lines(vals["id"], taxes)
        lines = []
        # Generate CREATE triplet
        for line_values in lines_values_list:
            line = (0, None, line_values)
            lines.append(line)
        
        # Return created account.move
        return self.with_context(check_move_validity=False).create({
            "biller_id" : vals["id"],
            "name" : vals["serie"] + "-" + str(vals["numero"]),
            "amount_total" : float(vals["total"]),
            "invoice_date" : datetime.strptime(vals["fecha_emision"], '%Y-%m-%d').date(),
            "state" : "draft", 
            "move_type" : REVERSE_CODES[vals["tipo_comprobante"]],
            "partner_id" : partner_id,
            "invoice_line_ids" : lines
        })
        
    
    def get_partner(self, vals):
        partner = self.env['res.partner'].search([
            ("fiscal_document_type", "=", vals["tipo_documento"].lower()),
            ("vat", "=", vals["documento"]),
            ])
        if partner:
            return partner
        else:
            return self.env['res.partner'].create({
                'name' : vals["razon_social"],
                'vat' : vals["documento"],
                'fiscal_document_type' : vals["tipo_documento"].lower(),
                'street' : vals["sucursal"]["direccion"],
                'city' : vals["sucursal"]["ciudad"],
                'country_id' : self.env['res.country'].search([("code", "=",  vals["sucursal"]["pais"])]).id
                })

    def get_received_lines(self, biller_id, tax):
        biller_proxy = self.env['biller.record']
        _, pdf_blocks = biller_proxy.get_biller_pdf(biller_id, self.env.company.access_token)
        item_blocks = pdf_blocks[10:]
        lines = []
        for item in item_blocks:
            try:
                elements = item[4].split("\n")
                if "Subtotal" in elements[1]:
                    break
                i=1
                while len(elements) > 5:
                    elements[0] += " " + elements[i]
                    elements.pop(i)
                    i+=1
                product = self.get_product(elements[0])

                if len(elements) == 3:
                    price_unit = elements[1].replace(".","")
                    price_unit = float(price_unit.replace(",","."))
                    line = {
                        'product_id' : product,
                        'price_unit' : price_unit,
                        'tax_ids' : [(4, tax, 0)]
                    }
                    lines.append(line)
                elif len(elements) == 5:
                    price_unit = elements[1].replace(".","")
                    price_unit = float(price_unit.replace(",","."))
                    quantity = elements[2].replace(".","")
                    quantity =  float(quantity.replace(",","."))
                    line = {
                        'product_id' : product,
                        'quantity' : quantity,
                        'price_unit' : price_unit,
                        'tax_ids' : [(4, tax, 0)]

                    }
                    lines.append(line)
            except:
                continue
        return lines
                

    def get_product(self, name):
        product = self.env['product.product'].search([("name", "=", name)])
        if product:
            return product
        tax_ids = self.env['account.tax'].search([
            ("type_tax_use", "=", "purchase"),
            ("company_id", "=", self.env.company.id),
        ]).ids
        return self.env['product.product'].create({
            'name': name,
            'purchase_ok': True,
            'detailed_type': "consu",
            'supplier_taxes_id': [(6, 0, tax_ids)]
        })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
