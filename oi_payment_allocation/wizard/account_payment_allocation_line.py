'''
Created on Oct 20, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class PaymentAllocationLines(models.TransientModel):
    _name = "account.payment.allocation.line"
    _description ='Payment Allocation Line'
    
    allocation_id = fields.Many2one('account.payment.allocation', required = True, ondelete='cascade')
    type = fields.Selection([('invoice', 'Invoice'), ('payment', 'Payment'), ('other', 'Other'), ('transfer_outbound','Transfer Out'), ('transfer_inbound','Transfer In')])
    
    move_line_id = fields.Many2one('account.move.line', required = True, ondelete = 'cascade')
   
    company_currency_id = fields.Many2one(related='move_line_id.company_currency_id')
    move_currency_id = fields.Many2one('res.currency',compute = '_calc_move_currency_id')
    allocation_currency_id = fields.Many2one(related='allocation_id.currency_id')
        
    amount_residual = fields.Monetary(compute ='_calc_amount_residual', currency_field = 'allocation_currency_id')
    partner_id = fields.Many2one(related='move_line_id.partner_id')
    ref = fields.Char(related='move_line_id.ref', readonly = True)
    name = fields.Char(related='move_line_id.name', readonly = True)
    date_maturity = fields.Date(related='move_line_id.date_maturity', readonly = True)
    date = fields.Date(related='move_line_id.date', readonly = True)
        
    allocate = fields.Boolean()
    allocate_amount = fields.Monetary(currency_field = 'allocation_currency_id')
    
    payment_id = fields.Many2one(related='move_line_id.payment_id', readonly = True, string='Payment')
    move_id = fields.Many2one(related='move_line_id.move_id', readonly = True)
    balance = fields.Monetary(compute = '_calc_balance', currency_field = 'move_currency_id')
    
    payment_date = fields.Date(related='payment_id.date', readonly = True, string='Payment Date')
    payment_amount = fields.Monetary(compute = '_calc_payment_amount', currency_field = 'move_currency_id')
    
    date_invoice = fields.Date(related='move_id.invoice_date', readonly = True)
    invoice_amount = fields.Monetary(compute = "_calc_invoice_amount", currency_field = 'move_currency_id')
    
    amount_residual_display = fields.Monetary(compute = '_calc_amount_residual_display', string='Unallocated Amount', currency_field = 'allocation_currency_id')
    
    sign = fields.Integer(compute = "_calc_sign")
    
    document_name = fields.Char(compute = '_calc_document_name')
    
    refund = fields.Boolean(compute = '_calc_refund')
    
    @api.depends('move_id.move_type')
    def _calc_refund(self):
        for record in self:
            record.refund = record.move_id.move_type in ['out_refund', 'in_refund']
    
    @api.depends('payment_id', 'move_id')
    def _calc_document_name(self):
        for record in self:
            record.document_name = record.payment_id.display_name or record.move_id.display_name
    
    @api.depends('move_line_id')
    def _calc_move_currency_id(self):
        for record in self:
            record.move_currency_id = record.move_line_id.currency_id or record.move_line_id.company_currency_id
    
    @api.depends('move_line_id', 'allocation_currency_id', 'allocation_id.line_ids.allocate')
    def _calc_amount_residual(self):

        manual_currency_rate = self._context.get('manual_currency_rate') or {}
        
        if 'currency_rate' in self.env['account.payment'] and self._context.get("active_model") == 'account.payment':
            payment_ids = self.env['account.payment'].browse(self._context.get('active_ids'))
            for payment in payment_ids:
                if payment.currency_rate:
                    manual_currency_rate[payment.currency_id.id] = payment.currency_rate
                
        if 'currency_rate' in self.env['account.move'] and self._context.get("active_model") == 'account.move':
            invoice_ids = self.env['account.move'].browse(self._context.get('active_ids'))
            for invoice in invoice_ids:
                if invoice.currency_rate and invoice.move_type in ['out_refund', 'in_refund']:
                    manual_currency_rate[invoice.currency_id.id] = invoice.currency_rate                
                         
        for record in self:
            max_date = max(record.allocation_id.line_ids.filtered('allocate').mapped('move_line_id.date') or [fields.Date.today()])
            
            if record.allocation_currency_id == record.company_currency_id:
                record.amount_residual = record.move_line_id.amount_residual
            elif record.allocation_currency_id == record.move_currency_id:
                record.amount_residual = record.move_line_id.amount_residual_currency
            elif record.move_line_id.currency_id:
                record.amount_residual = record.move_currency_id.with_context(manual_currency_rate = manual_currency_rate)._convert(record.move_line_id.amount_residual_currency, record.allocation_currency_id, record.allocation_id.company_id, max_date)
            else:
                record.amount_residual = record.company_currency_id.with_context(manual_currency_rate = manual_currency_rate)._convert(record.move_line_id.amount_residual, record.allocation_currency_id, record.allocation_id.company_id, max_date)
                
    @api.depends('move_line_id')
    def _calc_balance(self):
        for record in self:
            record.balance = record.move_line_id.currency_id and record.move_line_id.amount_currency or record.move_line_id.balance
    
    @api.depends('type','allocation_id', 'move_id.move_type')
    def _calc_sign(self):
        for record in self:
            if record.type == 'transfer_outbound':
                sign = 1
            elif record.type == 'transfer_inbound':
                sign = -1
            else:
                sign = (record.type in ['invoice', 'other'] and -1 or 1) * (record.allocation_id.account_id.user_type_id.type == 'payable' and 1 or -1)
            
            record.sign = sign
            
    @api.depends('sign','balance')
    def _calc_payment_amount(self):
        for record in self:
            record.payment_amount = record.balance * record.sign
            
    @api.depends('sign','balance')
    def _calc_invoice_amount(self):
        for record in self:
            record.invoice_amount = record.balance * record.sign
            
    
    @api.depends('amount_residual','sign')
    def _calc_amount_residual_display(self):
        for record in self:
            record.amount_residual_display = record.amount_residual * record.sign
    
    @api.onchange('allocate','amount_residual_display')
    def _calc_allocate_amount(self):
        line_ids = self.allocation_id.invoice_line_ids + self.allocation_id.payment_line_ids + self.allocation_id.other_line_ids
        other_lines = line_ids.filtered(lambda line : line !=self and line.allocate)
        total = 0
        for line in other_lines:
            total += line.allocate_amount * line.sign 
        
        total = total * self.sign
        
        if total < 0:
            total = abs(total)
        else:
            total = 0
        
        if not self.allocate:
            self.allocate_amount = 0
        elif total:
            self.allocate_amount = min(self.amount_residual_display, total)
        else:
            self.allocate_amount = self.amount_residual_display
                        
    @api.onchange('allocate_amount')
    def _onchange_allocate_amount(self):
        self.allocation_id._calc_balance()
