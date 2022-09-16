# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMoveReversal(models.TransientModel):

    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        res = super(AccountMoveReversal,self).reverse_moves()
        for move in self.new_move_ids:
            move.associated_move_ids = self.move_ids
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
