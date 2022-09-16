# -*- encoding: utf-8 -*-

import http.client
import json

CODES = {
    'out_invoice' : 111,
    'in_invoice' : 111,
    'out_refund' : 112,
}

ID_TYPE = {
    'rut' : 2,
    'ci' : 3,
    'others' : 4,
    'passport' : 5,
    'nin' : 6,
    'nife' : 7
}

class GenericDocumentSend(object):
    
    def __init__(self):
        pass

    def post_document(self, document, doc_id, company):
        conn = http.client.HTTPSConnection("{{test.biller.uy}}")
        items=[]
        for line in document.invoice_lines_ids:
            line_vals = {
                "cantidad": line.quantity,
                "concepto": line.name,
                "precio": line.price_unit,
                "indicador_facturacion": line.invoicing_indicator,
                "recargo_tipo": "%",
                "recargo_cantidad": line.discount,          
            }
            items.append(line_vals)
        payload = json.dumps({
            "tipo_comprobante": doc_id,
            "forma_pago": 1,
            "sucursal": company.branch_office,
            "moneda": document.currency_id.name,
            "montos_brutos": 1,
            "cliente": {
                "tipo_documento": document.partner_id.fiscal_document_type,
                "documento": document.partner_id.vat,
                "nombre_fantasia": document.partner_id.name,
            "sucursal": {
                "direccion": document.partner_id.street,
                "ciudad": document.partner_id.city,
                "departamento": document.partner_id.state_id,
                "pais": document.partner_id.country_id
                }
            },
            'items' : items,
            
            })



#@api.onchange("access_token")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
