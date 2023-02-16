# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CustomResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'modificar modelo de res_partner'

    type_invoice_usd = fields.Selection([('type_1', 'Tipo 1'), ('type_2', 'Tipo 2'), ('type_3', 'Tipo 3')],
                                    string='Tipo de Factura USD', default='type_1'
                                    )

    type_invoice_ves = fields.Selection([('type_1', 'Tipo 1'), ('type_2', 'Tipo 2')],
                                        string='Tipo de Factura Bs', default='type_1'
                                        )

    # type_invoice = fields.Char('xxxx')