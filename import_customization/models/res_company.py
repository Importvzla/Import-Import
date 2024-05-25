# -*- coding: utf-8 -*-

from odoo import fields, models


class CustomResCompany(models.Model):
    _inherit = 'res.company'
    _description = "Modificar modulo de res company para facturas de import import"

    inc_logo = fields.Binary(string="Logo Factura INC")
