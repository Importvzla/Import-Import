# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomAccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'modificar modelo de account_move'

    sale_order_id = fields.Many2one('sale.order', compute='_search_sale_order', store=True)
    # picking_out = fields.Char('picking id', compute='_search_picking_out', store=True)


#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
    @api.depends('invoice_origin')
    def _search_sale_order(self):
        for record in self:
            # template_id = self.env['mail.template'].search(
            #     [('id', '=', template_id)]).id
            if record.invoice_origin:
                so = record.env['sale.order'].search(
                    [('name', '=', record.invoice_origin)])
                record.sale_order_id = so.id
            else:
                record.sale_order_id = False

    # @api.depends('sale_order_id')
    # def _search_picking_out(self):
    #     for record in self:
    #         if record.sale_order_id:
    #             picking_ids = record.env['stock_picking'].search(
    #                 ['origin', '=', record.invoice_origin])
    #             out = record.sale_order_id.picking_ids.filtered(lambda r: r.picking_type_sequence_code == "OUT")
    #             print(out)
    #             record.picking_out = "asd"
    #         else:
    #             record.picking_out = False

