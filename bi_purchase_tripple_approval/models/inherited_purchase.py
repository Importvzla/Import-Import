# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
            ('draft', 'RFQ'),
            ('sent', 'RFQ Sent'),
            ('to approve', 'To Approve'),
            ('to second approval','To Second Approval'),
            ('purchase', 'Purchase Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    def button_confirm(self):
        res = self.env['res.config.settings'].sudo().search([], order="id desc", limit=1)
        if res.po_order_approval == True and self.amount_total > res.po_double_validation_amount :
            self.write({'state': 'to approve'})
        else : 
            return super(PurchaseOrder, self).button_confirm()
        return True
 
    def button_approve_custom(self, force=False):
        res = self.env['res.config.settings'].sudo().search([], order="id desc", limit=1)
        if res.second_approval == True and self.amount_total > res.second_approval_minimum_amount :
            self.write({'state' :'to second approval'})
        else :
            return self.button_approve(force=False)
        return {}

    def button_second_approve(self):
        for order in self :
            order.write({'state':'purchase','date_approve': fields.Date.context_today(self)})
            order._create_picking()
        return
