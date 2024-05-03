# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomAccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'modificar modelo de account_move'

    x_nota_entrega = fields.Many2many('stock.picking', 'stock_picking_account_move_rel', string='No Nota de Entrega',
                                     domain = "[('origin', '=', invoice_origin), ('picking_type_code', '=', 'outgoing')]")
    sale_order_id = fields.Many2one('sale.order', compute='_search_sale_order', store=True)
    # sale_order_number = fields.Char(string='N° Orden de Compra', compute='_search_sale_order_number', store=True)
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

    # @api.depends('invoice_origin')
    # def _search_sale_order_number(self):
    #     for record in self:
    #         if record.invoice_origin:
    #             sale_id = record.env['sale.order'].search([('name', '=', record.invoice_origin)])
    #             if sale_id:
    #                 record.sale_order_number = sale_id[0].x_ocompra
                