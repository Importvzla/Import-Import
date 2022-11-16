'''
Created on Oct 20, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PaymentAllocation(models.TransientModel):
    _name = "account.payment.allocation"
    _description ='Payment Allocation'
    
    @api.model
    def _get_payment(self):
        if self._context.get('active_model') == 'account.payment':
            return [(6,0, self._context.get('active_ids'))]
        
    @api.model
    def _get_invoice(self):
        if self._context.get('active_model') == 'account.move':
            return [(6,0, self._context.get('active_ids'))]
        
    @api.model
    def _get_currency_id(self):
        currency_id = self.env['res.currency']
        
        if self._context.get('active_model') == 'account.move':
            currency_id = self.env['account.move'].browse(self._context.get('active_ids')).mapped('currency_id')
            
        elif self._context.get('active_model') == 'account.payment':
            currency_id = self.env['account.payment'].browse(self._context.get('active_ids')).mapped('currency_id')
                
        currency_id -= self.env.company.currency_id
        if len(currency_id)==1:
            return currency_id            
        
        return self.env.company.currency_id        
    
    partner_id = fields.Many2one('res.partner', required = True)
    account_id = fields.Many2one('account.account', required = True)
    show_child = fields.Boolean('Show parent/children')    
    
    line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id')
    invoice_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id', domain = [('type', '=', 'invoice')])
    payment_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id', domain = [('type', '=', 'payment')])
    other_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id', domain = [('type', '=', 'other')])
    
    transfer_outbound_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id', domain = [('type', '=', 'transfer_outbound')])
    transfer_inbound_line_ids = fields.One2many('account.payment.allocation.line', 'allocation_id', domain = [('type', '=', 'transfer_inbound')])
    
    company_id = fields.Many2one('res.company', required = True, default = lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', required = True, default = _get_currency_id)
    
    balance = fields.Monetary(compute ='_calc_balance')
    
    payment_ids = fields.Many2many('account.payment', default = _get_payment)
    invoice_ids = fields.Many2many('account.move', default = _get_invoice)
    
    writeoff_acc_id = fields.Many2one('account.account', string='Write off Account')
    writeoff_journal_id = fields.Many2one('account.journal', string='Write off Journal')
    writeoff_ref = fields.Char('Write off Reference')
    
    create_entry = fields.Boolean('Create Account/Partner Entry')
    entry_journal_id = fields.Many2one('account.journal', string='Account/Partner Entry Journal')
    entry_name = fields.Char('Entry Reference')
    
    date_from = fields.Date()
    date_to = fields.Date()
    
    ref = fields.Char('Reference')
    
    @api.model
    def default_get(self, fields_list):
        if self._context.get("active_model") == 'account.move' and self.env['ir.config_parameter'].sudo().get_param('payment.allocation.invoice_disabled') == 'True' :
            invoice = self.env['account.invoice'].browse(self._context.get('active_id'))
            if invoice.move_type not in ['out_refund', 'in_refund']:
                raise UserError(_("Please use allocation from payment / credit notes"))
            
        return super(PaymentAllocation, self).default_get(fields_list)
    
    @api.onchange('account_id', 'partner_id', 'show_child', 'company_id', 'currency_id', 'date_from', 'date_to', 'ref')
    def _reset_lines(self):
        if self.account_id and self.partner_id:
            for line_type in ['invoice', 'payment', 'other','transfer_outbound','transfer_inbound']:
                fname = '%s_line_ids' % line_type
                self[fname] = False
                domain = [('account_id', '=', self.account_id.id), ('reconciled', '=', False), ('company_id', '=', self.company_id.id), ('parent_state','=', 'posted')]
                
                if self.date_from:
                    domain.append(('date', '>=', self.date_from))

                if self.date_to:
                    domain.append(('date', '<=', self.date_to))
                    
                if self.ref:
                    domain.append(('ref', 'ilike', self.ref))
                
                if self.show_child:
                    partner_id = self.partner_id
                    while partner_id.parent_id:
                        partner_id = partner_id.parent_id
                    domain.append(('partner_id', 'child_of', partner_id.ids))
                else:
                    domain.append(('partner_id', '=', self.partner_id.id))            
                if line_type == 'invoice':                        
                    domain.extend([('move_id.move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'])])
                elif line_type in ['payment', 'transfer_outbound','transfer_inbound']:
                    domain.append(('payment_id', '!=', False))     
                else:
                    domain.extend([('move_id.move_type', 'not in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']), ('payment_id', '=', False)])          
                                     
                for move_line in self.env['account.move.line'].search(domain):
                    if line_type == 'payment':
                        if move_line.payment_id.is_internal_transfer:
                            continue
                    elif line_type in ['transfer_outbound', 'transfer_inbound']:
                        if not move_line.payment_id.is_internal_transfer:
                            continue
                        if move_line.payment_id.payment_type != line_type[9:]:
                            continue                        

                    if self.env['ir.config_parameter'].sudo().get_param('payment.allocation.payment_only') == 'True' :
                        
                        if self.payment_ids:
                            if move_line.payment_id and move_line.payment_id not in self.payment_ids._origin:
                                continue
                            if move_line.move_id.move_type in ['out_refund', 'in_refund']:
                                continue
                        
                        if self.invoice_ids[:1].move_type in ['out_refund', 'in_refund']:
                            if move_line.payment_id:
                                continue
                            if  move_line.move_id.move_type in ['out_refund', 'in_refund'] and  move_line.move_id not in  self.invoice_ids:
                                continue
                    allocate = move_line.payment_id in self.payment_ids._origin or move_line.move_id in self.invoice_ids._origin
                                                            
                    new_line = self[fname].new({
                        'move_line_id' : move_line.id,
                        'allocate' : allocate,
                        'type' : line_type,
                        })
                    self[fname] += new_line
                    new_line._calc_allocate_amount()
                    
                    
    @api.onchange('payment_ids')         
    def _onchange_payment_ids(self):
        if self.payment_ids:
            self.account_id = self.payment_ids[0].destination_account_id
            self.partner_id = self.payment_ids[0].partner_id
            self._reset_lines()
            
    @api.onchange('invoice_ids')         
    def _onchange_invoice_ids(self):
        if self.invoice_ids:
            self.account_id = self.invoice_ids.mapped('line_ids.account_id').filtered(lambda account : account.user_type_id.type in ['receivable', 'payable'])[:1]
            self.partner_id = self.invoice_ids[0].partner_id
            self._reset_lines()
            
                    
    @api.depends('invoice_line_ids.allocate_amount', 'payment_line_ids.allocate_amount', 'other_line_ids.allocate_amount', 'transfer_outbound_line_ids.allocate_amount','transfer_inbound_line_ids.allocate_amount')
    def _calc_balance(self):
        for record in self:
            balance = 0
            for line in record.invoice_line_ids + record.payment_line_ids + record.other_line_ids + record.transfer_outbound_line_ids + record.transfer_inbound_line_ids:
                if line.allocate:
                    balance += line.allocate_amount * line.sign
            record.balance = balance
    
    def _prepare_exchange_diff_move(self, move_date):
        return {
            'move_type': 'entry',
            'date': move_date,
            'journal_id': self.company_id.currency_exchange_journal_id.id,
            'line_ids': [],
        }

    def validate(self):         
        if 'currency_rate' in self.env['account.payment']:
            manual_currency_rate = {}
            payment_line_ids = self.line_ids.filtered(lambda line : line.allocate and line.payment_id and line.move_currency_id != line.company_currency_id) 
            for line in payment_line_ids:    
                payment = line.payment_id            
                if payment.currency_rate:
                    manual_currency_rate[payment.currency_id.id] = payment.currency_rate
            if not payment_line_ids:
                refund_line_ids = self.line_ids.filtered(lambda line : line.allocate and line.invoice_id in ['in_refund', 'out_refund'] and line.move_currency_id != line.company_currency_id)
                for line in refund_line_ids:
                    refund = line.invoice_id            
                    if refund.currency_rate:
                        manual_currency_rate[refund.currency_id.id] = refund.currency_rate

            self = self.with_context(manual_currency_rate = manual_currency_rate)

        max_date = max(self.line_ids.filtered('allocate').mapped('move_line_id.date') or [fields.Date.today()])
        
        if self.balance and self.writeoff_acc_id and self.writeoff_journal_id:
            
            if self.currency_id != self.company_id.currency_id:
                currency_id = self.currency_id.id
                amount_currency = self.balance
                balance = self.currency_id._convert(amount_currency, self.company_id.currency_id, self.company_id, max_date)
            else:
                currency_id = False
                amount_currency = False
                balance = self.balance
                        
            move_vals= {
                'journal_id' : self.writeoff_journal_id.id,
                'ref': self.writeoff_ref or _('Write-Off'),
                'date' : max_date,
                'line_ids' : [
                        (0,0, {
                            'account_id' : self.account_id.id,
                            'partner_id' : self.partner_id.id,
                            'debit' : -balance if balance < 0 else 0,
                            'credit' : balance if balance > 0 else 0,
                            'currency_id' : currency_id,
                            'amount_currency' : -amount_currency
                            }),
                        (0,0, {
                            'account_id' : self.writeoff_acc_id.id,
                            'partner_id' : self.partner_id.id,
                            'credit' : -balance if balance < 0 else 0,
                            'debit' : balance if balance > 0 else 0,
                            'currency_id' : currency_id,
                            'amount_currency' : amount_currency           
                            })                        
                    ]
                }
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()            
            move_line_id = move_id.line_ids.filtered(lambda line : line.account_id == self.account_id)
            line = self.env["account.payment.allocation.line"].create({
                'allocation_id' : self.id,
                'type' : 'other',
                'move_line_id' : move_line_id.id,
                'allocate' : True,
                })
            line.allocate_amount = line.amount_residual_display
            
        
        debit_line_ids = self.line_ids.filtered(lambda line : line.allocate and line.allocate_amount and line.move_line_id.debit)
        credit_line_ids = self.line_ids.filtered(lambda line : line.allocate and line.allocate_amount and line.move_line_id.credit)
        if not debit_line_ids or not credit_line_ids:
            raise UserError('Select at least one payment & one invoice')
        
        move_line_ids = (debit_line_ids + credit_line_ids).mapped('move_line_id')
                                    
        partner_ids = move_line_ids.mapped('partner_id')
        partner_balance = False
        if len(partner_ids) > 1 and self.create_entry:
            partner_balance = dict.fromkeys(partner_ids.ids, 0)
        
        partial_reconcile_ids = self.env["account.partial.reconcile"]
        
        line_currency_diff = {}
        
        for debit_line in debit_line_ids:
            for credit_line in credit_line_ids:
                allocate_amount = min (debit_line.allocate_amount, credit_line.allocate_amount)
                if not allocate_amount:
                    continue
                                                                                                        
                vals = {
                    'debit_move_id' : debit_line.move_line_id.id,
                    'credit_move_id' : credit_line.move_line_id.id,                    
                    'amount' : self.currency_id._convert(allocate_amount, self.company_id.currency_id, self.company_id, max_date),                    
                    'debit_amount_currency' : self.currency_id._convert(allocate_amount, debit_line.move_line_id.currency_id, self.company_id, max_date),
                    'credit_amount_currency' : self.currency_id._convert(allocate_amount, credit_line.move_line_id.currency_id, self.company_id, max_date)
                    }
                                                
                for n in range(2):                                
                    for line, amount_currency, sign in [(debit_line,vals['debit_amount_currency'],1) , (credit_line,vals['credit_amount_currency'], -1)]:
                        if line.move_line_id.amount_currency:
                            rate = line.move_line_id.amount_currency / line.move_line_id.balance
                            old_amount = amount_currency / rate
                            diff_amount = self.company_id.currency_id.round((old_amount - vals['amount'])  * sign)                 
                            if n==0 and (diff_amount * sign) < 0:
                                vals['amount'] =  self.company_id.currency_id.round(vals['amount'] + (diff_amount * sign))
                            if n==1:  
                                line_currency_diff[line.move_line_id] = diff_amount                    
                    
                partial_reconcile_ids += self.env["account.partial.reconcile"].create(vals)
                if partner_balance:
                    partner_balance[debit_line.move_line_id.partner_id.id] += allocate_amount
                    partner_balance[credit_line.move_line_id.partner_id.id] -= allocate_amount
                
                debit_line.allocate_amount -= allocate_amount * (debit_line.allocate_amount < 0 and -1 or 1)
                credit_line.allocate_amount -= allocate_amount * (credit_line.allocate_amount < 0 and -1 or 1)            
        
        exchange_lines = []
        exchange_move = self.env['account.move']
        exchange_partial_reconcile = self.env["account.partial.reconcile"]
        exchange_lines_to_rec = self.env['account.move.line']

        for move_line in move_line_ids:
            if not move_line.amount_currency:
                continue
            if not move_line.amount_residual_currency and not move_line.amount_residual:
                continue
            
            if not move_line.amount_residual_currency and move_line.amount_residual:
                amount = move_line.amount_residual
            elif move_line in line_currency_diff:
                amount = line_currency_diff[move_line]
            else:
                amount = move_line.amount_residual - move_line.currency_id._convert(move_line.amount_residual_currency, self.company_id.currency_id, self.company_id, max_date)
            
            amount = self.company_id.currency_id.round(amount)
            if amount:
                exchange_lines.append((move_line, amount))      
                                
        if exchange_lines:
            exchange_move = self.env['account.move'].create(self._prepare_exchange_diff_move(move_date=max_date))
            exchange_journal = exchange_move.journal_id
            for move_line, amount in exchange_lines:
                line_to_rec = self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'name': _('Currency exchange rate difference'),
                    'debit' : -amount if amount < 0 else 0,
                    'credit' : amount if amount > 0 else 0, 
                    'account_id' : move_line.account_id.id,
                    'move_id' : exchange_move.id,
                    'partner_id': move_line.partner_id.id,
                    'amount_currency' : 0,
                    'currency_id' : move_line.currency_id.id
                    })
                
                account_id = amount > 0 and self.company_id.expense_currency_exchange_account_id.id or self.company_id.income_currency_exchange_account_id.id
                if "currency.exchange.account" in self.env:
                    curency_exchange_account_id = self.env['currency.exchange.account'].search([('currency_id','=', move_line.currency_id.id), ('journal_id','=',exchange_journal.id)])
                    if curency_exchange_account_id.account_id:
                        account_id = curency_exchange_account_id.account_id.id
                        
                exchange_lines_to_rec += line_to_rec
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'name': _('Currency exchange rate difference'),
                    'debit' : amount if amount > 0 else 0, 
                    'credit' : -amount if amount < 0 else 0,
                    'account_id': account_id,
                    'move_id': exchange_move.id,
                    'partner_id': move_line.partner_id.id,
                    'amount_currency' : 0,
                    'currency_id' : move_line.currency_id.id                    
                    })
                exchange_partial_vals = {
                    'debit_move_id' : line_to_rec.id if line_to_rec.debit else move_line.id,
                    'credit_move_id' : line_to_rec.id if line_to_rec.credit else move_line.id,
                    'amount' : abs(amount),
                    'debit_amount_currency' : 0,
                    'credit_amount_currency' : 0,                    
                    }
                if (move_line.id == exchange_partial_vals['debit_move_id'] and move_line.credit) or (move_line.id == exchange_partial_vals['credit_move_id'] and move_line.debit):
                    exchange_partial_vals.update({
                        'amount' : -exchange_partial_vals['amount'],
                        'debit_move_id' : exchange_partial_vals['credit_move_id'],
                        'credit_move_id' : exchange_partial_vals['debit_move_id']
                        })
                    
                exchange_partial_reconcile += self.env["account.partial.reconcile"].create(exchange_partial_vals)
            exchange_move.post()
        
        reconciled_move_line_ids = move_line_ids.filtered('reconciled') + exchange_lines_to_rec
        if reconciled_move_line_ids:            
            partial_reconcile_ids = partial_reconcile_ids.filtered(lambda record : record.debit_move_id in reconciled_move_line_ids or record.credit_move_id in reconciled_move_line_ids) + exchange_partial_reconcile
            self.env["account.full.reconcile"].create({
                'partial_reconcile_ids' : [(6,0, partial_reconcile_ids.ids)],
                'reconciled_line_ids' : [(6,0, reconciled_move_line_ids.ids)],
                'exchange_move_id' : exchange_move.id
                })                                    
        
        if partner_balance:
            move_vals= {
                'journal_id' : self.entry_journal_id.id,
                'ref': self.entry_name or 'Payment Allocation',
                'date' : max_date,
                'line_ids' : []
                }
            for partner_id, balance in partner_balance.items():
                if not balance:
                    continue

                if self.currency_id != self.company_id.currency_id:
                    currency_id = self.currency_id.id
                    amount_currency = balance
                    balance = self.currency_id._convert(amount_currency, self.company_id.currency_id, self.company_id, max_date)
                else:
                    currency_id = False
                    amount_currency = False
                
                move_vals['line_ids'].append((0,0, {
                    'account_id': self.account_id.id,
                    'name' : '',
                    'partner_id' : partner_id,
                    'credit' : balance > 0 and balance or 0,
                    'debit' : balance < 0 and -balance or 0,
                    'currency_id' : currency_id,
                    'amount_currency' : amount_currency
                    }))
            move_id=self.env['account.move'].create(move_vals)
            move_id.post()
            move_id.line_ids.reconcile()
            move_line_ids +=  move_id.line_ids   

        return {
            'type' : 'ir.actions.act_window_close'
            }
            
