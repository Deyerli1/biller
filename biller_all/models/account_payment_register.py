# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import http.client
import json


class AccountPaymentRegister(models.TransientModel):

    _inherit = 'account.payment.register'

    def action_create_payments(self):

        res = super(AccountPaymentRegister, self).action_create_payments()
        original_move = self.env['account.move'].browse(self.env.context['active_ids'])
        payload = self.get_payload()
        biller_proxy = self.env['biller.record']
        biller_proxy.post_document(payload, 'payment_sent')

        raise ValidationError("AAAAAAAAAAAAA")

        return res

    def get_payload(self,):
        payload = json.dumps({
            "referencias": [
                {
                    "padre": 79508,
                    "total": 1200
                },
                {
                    "padre": 79509,
                    "total": 600
                }
            ],
            "pago": {
                "fecha": "2021-05-27",
                "monto": 1800,
                "referencia": "Transferencia Itaú 2185"
            }
        })
        return payload


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
