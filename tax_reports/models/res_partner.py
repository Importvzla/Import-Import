# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions, _


class CustomResPartner(models.Model):
    _inherit = 'res.partner'
    _description = "Modificar modulo de res partner"

    third_party_account_payment = fields.Boolean(string='Pago Cuenta de Tercero', default=False)
