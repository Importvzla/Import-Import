# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomAccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'modificar modelo de account_move'

    sale_order_id = fields.Many2one('sale.order', compute='_search_sale_order', store=True)
    rate = fields.Float(related='currency_id.rate', store=True)
    amount_untaxed_rate = fields.Float(compute='_compute_amount_untaxed', store=True)
    amount_tax_rate = fields.Float(compute='_compute_amount_tax_rate', store=True)
    amount_total_rate = fields.Float(compute='_compute_amount_total_rate', store=True)

    @api.depends('amount_untaxed', 'x_tasa')
    def _compute_amount_untaxed(self):
        for record in self:
            print(record)
            if record.currency_id.name != 'VEF':
                if record.rate and record.rate != 0:
                    record.amount_untaxed_rate = record.amount_untaxed * record.x_tasa
                else:
                    record.amount_untaxed_rate = False

    @api.depends('amount_tax', 'x_tasa')
    def _compute_amount_tax_rate(self):
        for record in self:
            print(record)
            if record.currency_id.name != 'VEF':
                if record.rate and record.rate != 0:
                    record.amount_tax_rate = record.amount_tax * record.x_tasa
                else:
                    record.amount_tax_rate = False

    @api.depends('amount_total', 'x_tasa')
    def _compute_amount_total_rate(self):
        for record in self:
            print(record)
            if record.currency_id.name != 'VEF':
                if record.rate and record.rate != 0:
                    record.amount_total_rate = record.amount_total * record.x_tasa
                else:
                    record.amount_total_rate = False
    # picking_out = fields.Char('picking id', compute='_search_picking_out', store=True)

    # @api.depends('invoice_origin')
    # def _search_currency_rate(self):
    #     for record in self:
    #         print(record)
    #         # template_id = self.env['mail.template'].search(
    #         #     [('id', '=', template_id)]).id
    #         # if record.invoice_origin:
    #         #     so = record.env['sale.order'].search(
    #         #         [('name', '=', record.invoice_origin)])
    #         #     record.sale_order_id = so.id
    #         # else:
    #         #     record.sale_order_id = False

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

