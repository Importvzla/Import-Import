# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions, _


class CustomAccountMove(models.Model):
    _inherit = 'account.move'
    _description = "Modificar modulo de account move"

    third_party_account_payment = fields.Boolean(related='partner_id.third_party_account_payment')
    fiscal_provider = fields.Many2one('res.partner', compute='select_provider', store=True, string='Proveedor Fiscal', readonly=False)

    @api.depends('partner_id')
    def select_provider(self):
        for record in self:
            record.fiscal_provider = record.partner_id.id

