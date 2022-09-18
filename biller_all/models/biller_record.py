# -*- encoding: utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields
from odoo.exceptions import UserError, ValidationError
import http.client

class BillerRecord(models.Model):
    _name = 'biller.record'
    _description = "Model to keep track of sent and received biller messages"
    
    document_type = fields.Selection([
        ('cfe_sent', 'Factura Enviada'),
        ('cfe_received', 'Factura Recibida'),
        ('payment_sent', 'Pago enviado'),], 
        readonly=True,
        string = "Tipo de documento"
    )

    name = fields.Char("Documento Origen", copy=False,readonly=True)

    payload = fields.Text("Payload", copy=False,readonly=True)

    response = fields.Text("Respuesta", copy=False,readonly=True)

    response_date = fields.Datetime("Fecha de creación", copy=False,readonly=True)

    def get_response(self, type, request_string, payload):
        conn = http.client.HTTPSConnection("test.biller.uy")
        authorization = 'Bearer {}'.format(self.env.company.access_token)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': authorization
        }
        conn.request(type, request_string, payload, headers)
        return conn.getresponse()

    def post_document(self, payload, type):
        res = self.get_response("POST","/v2/comprobantes/crear",payload)
        data = res.read()
        self.create({
            'name' : eval(data.decode())["serie"] + "-" + str(eval(data.decode())["numero"]) if res.code == 201 else "Error",
            'document_type' : type,
            'payload' : payload,
            'response' : data,
            'response_date' : datetime.now()
        })
        self.env.cr.commit()
        return res, data

    def get_sent_documents(self, doc_id, branch_office, date_from, date_to):
        doc_id = ("id=" + str(doc_id)+ "&") if doc_id else ''
        branch_office = ("sucursal=" + str(branch_office) + "&") if branch_office else ''
        date_from = date_from.strftime("%Y-%m-%d") if date_from else fields.Date.today().strftime("%Y-%m-%d")
        date_to = date_to.strftime("%Y-%m-%d") if date_to else fields.Date.today().strftime("%Y-%m-%d")
        request_string = "/v2/comprobantes/obtener?{}{}desde={}%2000:00:00&hasta={}%2023:59:59".format(doc_id, branch_office, date_from, date_to)
        payload = ''
        res = self.get_response("GET", request_string, payload)
        data = res.read()
        return self.create({
            'name' : "Obtener comprobantes {}".format(datetime.now().strftime("%d/%m/%Y %H:%M")),
            'document_type' : 'cfe_received',
            'payload' : payload,
            'response' : data if bool(data) else "No hubo comprobantes en el rango especificado de {} a {}".format(date_from, date_to),
            'response_date' : fields.Date.today()
        })

    def get_received_documents(self, date_from, date_to):
        date_from = date_from.strftime("%Y-%m-%d") if date_from else fields.Date.today().strftime("%Y-%m-%d")
        date_to = date_to.strftime("%Y-%m-%d") if date_to else (fields.Date.today() - relativedelta(days=1)).strftime("%Y-%m-%d")
        request_string = "/v2/comprobantes/recibidos/obtener?fecha_desde={}&fecha_hasta={}".format(date_from, date_to)
        payload = ''
        res = self.get_response("GET", request_string, payload)
        data = res.read()
        return self.create({
            'name' : "Obtener comprobantes {}".format(datetime.now().strftime("%d/%m/%Y %H:%M")),
            'document_type' : 'cfe_received',
            'payload' : payload,
            'response' : data if bool(data) else "No hubo comprobantes en el rango especificado de {} a {}".format(date_from, date_to),
            'response_date' : fields.Date.today()
        })

    def get_biller_pdf(self, biller_id):
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://test.biller.uy/comprobantes/pdf/{}'.format(biller_id),
            'target': 'new',
        }



        
        

        


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
