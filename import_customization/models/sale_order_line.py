# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CustomSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'modificar modelo Sale Order Line'



    x_tasa_venta = fields.Float(related='order_id.x_studio_tasa_venta', readonly=True, string="Tasa", digits=(12,4))
    x_npedido = fields.Char(related='order_id.x_npedido', readonly=True, string="No Pedido")
    x_n_orden_de_compra = fields.Char(related='order_id.x_studio_n_orden_de_compra', readonly=True, string="OC Cliente")
    date_order = fields.Datetime(related='order_id.date_order', readonly=True, string="Fecha de Pedido")
    pricelist_id = fields.Many2one(related='order_id.pricelist_id', readonly=True)
    price_unit_rate = fields.Float(compute='cal_price_rate', string='Precio Unitario ($)', digits='Product Price', readonly=True, store=True)
    price_subtotal_rate = fields.Float(compute='cal_price_rate', string='Subtotal ($)', digits='Product Price', readonly=True, store=True)

    @api.depends('x_tasa_venta', 'pricelist_id', 'price_unit', 'price_subtotal')
    def cal_price_rate(self):
        for record in self:
            if record.pricelist_id.currency_id.name == 'VES':
                record.price_unit_rate = round(record.price_unit / record.x_tasa_venta, 2)
                record.price_subtotal_rate = round(record.price_subtotal / record.x_tasa_venta, 2)