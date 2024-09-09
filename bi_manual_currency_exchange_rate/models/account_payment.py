# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError, ValidationError


class account_payment(models.TransientModel):
    _inherit = 'account.payment.register'

    manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
    manual_currency_rate = fields.Float('Rate', digits=(12, 6))

    @api.model
    def default_get(self, default_fields):
        rec = super(account_payment, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec
        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda move: move.is_invoice(include_receipts=True))
        if len(invoices or []) > 1:
            if all(inv.manual_currency_rate_active == False for inv in invoices):
                return rec
            if any(inv.manual_currency_rate_active == False for inv in invoices):
                raise ValidationError(_("Selected invoice to make payment have not similer currency or currency rate is not same.\n Make sure selected invoices have same currency and same manual currency rate."))
            else:
                rate = invoices[0].manual_currency_rate
                if any(inv.manual_currency_rate != rate for inv in invoices):
                    raise ValidationError(_("Selected invoice to make payment have not similer currency or currency rate is not same.\n Make sure selected invoices have same currency and same manual currency rate."))
        rec.update({
            'manual_currency_rate_active': invoices[0].manual_currency_rate_active,
            'manual_currency_rate': invoices[0].manual_currency_rate
        })
        return rec

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.manual_currency_rate_active:
            vals.update({'manual_currency_rate_active': self.manual_currency_rate_active, 'manual_currency_rate': self.manual_currency_rate})
        return vals
    
    @api.depends('can_edit_wizard', 'source_amount', 'source_amount_currency', 
    'source_currency_id', 'company_id', 'currency_id', 'payment_date',
    'manual_currency_rate_active', 'manual_currency_rate')
    def _compute_amount(self):
        return super()._compute_amount()

    @api.depends('can_edit_wizard', 'amount',
    'manual_currency_rate_active', 'manual_currency_rate')
    def _compute_payment_difference(self):
        return super()._compute_payment_difference()

    def _get_total_amount_in_wizard_currency_to_full_reconcile(self, batch_result, early_payment_discount=True):
        """ Compute the total amount needed in the currency of the wizard to fully reconcile the batch of journal
        items passed as parameter.

        :param batch_result:    A batch returned by '_get_batches'.
        :return:                An amount in the currency of the wizard.
        """
        self.ensure_one()
        comp_curr = self.company_id.currency_id

        if self.source_currency_id == self.currency_id:
            # Same currency (manage the early payment discount).
            return self._get_total_amount_using_same_currency(batch_result, early_payment_discount=early_payment_discount)
        elif self.source_currency_id != comp_curr and self.currency_id == comp_curr:
            # Foreign currency on source line but the company currency one on the opposite line.
            if self.manual_currency_rate_active and self.manual_currency_rate:
                return (self.source_amount_currency / self.manual_currency_rate), False
            else:
                return self.source_currency_id._convert(
                    self.source_amount_currency,
                    comp_curr,
                    self.company_id,
                    self.payment_date,
                ), False
        elif self.source_currency_id == comp_curr and self.currency_id != comp_curr:
            # Company currency on source line but a foreign currency one on the opposite line.
            if self.manual_currency_rate_active and self.manual_currency_rate:
                return abs(sum((aml.amount_residual * self.manual_currency_rate) for aml in batch_result['lines']
                )), False
            else:
                return abs(sum(
                    comp_curr._convert(
                        aml.amount_residual,
                        self.currency_id,
                        self.company_id,
                        aml.date,
                    )
                    for aml in batch_result['lines']
                )), False
        else:
            # Foreign currency on payment different than the one set on the journal entries.
            if self.manual_currency_rate_active and self.manual_currency_rate:
                return self.source_amount * self.manual_currency_rate, False
            else:
                return comp_curr._convert(
                    self.source_amount,
                    self.currency_id,
                    self.company_id,
                    self.payment_date,
                ), False
    

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            'manual_currency_rate' : self.manual_currency_rate,
            'manual_currency_rate_active' : self.manual_currency_rate_active,
            'write_off_line_vals': [],
        }

        if self.manual_currency_rate_active and self.manual_currency_rate:
            conversion_rate = self.manual_currency_rate
        else:
            conversion_rate = self.env['res.currency']._get_conversion_rate(
                self.currency_id,
                self.company_id.currency_id,
                self.company_id,
                self.payment_date,
            )

        if self.payment_difference_handling == 'reconcile':

            if self.early_payment_discount_mode:
                epd_aml_values_list = []
                for aml in batch_result['lines']:
                    if aml.move_id._is_eligible_for_early_payment_discount(self.currency_id, self.payment_date):
                        epd_aml_values_list.append({
                            'aml': aml,
                            'amount_currency': -aml.amount_residual_currency,
                            'balance': aml.company_currency_id.round(-aml.amount_residual_currency * conversion_rate),
                        })

                open_amount_currency = self.payment_difference * (-1 if self.payment_type == 'outbound' else 1)
                open_balance = self.company_id.currency_id.round(open_amount_currency * conversion_rate)
                early_payment_values = self.env['account.move']._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list, open_balance)
                for aml_values_list in early_payment_values.values():
                    payment_vals['write_off_line_vals'] += aml_values_list

            elif not self.currency_id.is_zero(self.payment_difference):
                if self.payment_type == 'inbound':
                    # Receive money.
                    write_off_amount_currency = self.payment_difference
                else:
                    # Send money.
                    write_off_amount_currency = -self.payment_difference

                write_off_balance = self.company_id.currency_id.round(write_off_amount_currency * conversion_rate)
                payment_vals['write_off_line_vals'].append({
                    'name': self.writeoff_label,
                    'account_id': self.writeoff_account_id.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.currency_id.id,
                    'amount_currency': write_off_amount_currency,
                    'balance': write_off_balance,
                })

        return payment_vals

class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Payments"

    manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
    manual_currency_rate = fields.Float('Rate', digits=(12, 6))
    amount_currency = fields.Float('Amount Currency')
    check_active_currency = fields.Boolean('Check Active Currency')

    @api.onchange('manual_currency_rate_active', 'currency_id')
    def check_currency_id(self):
        for payment in self:
            if payment.manual_currency_rate_active:
                if payment.currency_id == payment.company_id.currency_id:
                    payment.manual_currency_rate_active = False
                    raise UserError(_('Company currency and Payment currency same, You can not add manual Exchange rate for same currency.'))

    @api.model
    def default_get(self, default_fields):

        rec = super(AccountPayment, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec

        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda move: move.is_invoice(include_receipts=True))


        if (len(invoices) == 1):
            rec.update({
                'manual_currency_rate_active': invoices.manual_currency_rate_active,
                'manual_currency_rate': invoices.manual_currency_rate,
            })
        return rec

    @api.model
    def _compute_payment_amount(self, invoices, currency, journal, date):
        '''Compute the total amount for the payment wizard.
        :param invoices:    Invoices on which compute the total as an account.invoice recordset.
        :param currency:    The payment's currency as a res.currency record.
        :param journal:  The payment's journal as an account.journal record.
        :param date:        The payment's date as a datetime.date object.
        :return:            The total amount to pay the invoices.
        '''
        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id
        date = date or fields.Date.today()

        if not invoices:
            return 0.0

        self.env['account.move'].flush(['type', 'currency_id'])
        self.env['account.move.line'].flush(['amount_residual', 'amount_residual_currency', 'move_id', 'account_id'])
        self.env['account.account'].flush(['user_type_id'])
        self.env['account.account.type'].flush(['type'])
        self._cr.execute('''
                SELECT
                    move.type AS type,
                    move.currency_id AS currency_id,
                    SUM(line.amount_residual) AS amount_residual,
                    SUM(line.amount_residual_currency) AS residual_currency
                FROM account_move move
                LEFT JOIN account_move_line line ON line.move_id = move.id
                LEFT JOIN account_account account ON account.id = line.account_id
                LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
                WHERE move.id IN %s
                AND account_type.type IN ('receivable', 'payable')
                GROUP BY _prepare_move_line_default_valsmove.id, move.type
            ''', [tuple(invoices.ids)])
        query_res = self._cr.dictfetchall()

        total = 0.0
        for inv in invoices:
            for res in query_res:
                move_currency = self.env['res.currency'].browse(res['currency_id'])
                if move_currency == currency and move_currency != company.currency_id:
                    total += res['residual_currency']
                else:
                    if not inv.manual_currency_rate_active:
                        total += company.currency_id._convert(res['amount_residual'], currency, company, date)
                    else:
                        total += res['residual_currency'] * inv.manual_currency_rate
        return total

    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'payment_type', 'manual_currency_rate')
    def _compute_payment_difference(self):
        draft_payments = self.filtered(lambda p: p.invoice_ids and p.state == 'draft')
        for pay in draft_payments:
            payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
            pay.payment_difference = pay._compute_payment_amount(pay.invoice_ids, pay.currency_id, pay.journal_id,
                                                                 pay.payment_date) - payment_amount
        (self - draft_payments).payment_difference = 0

    def _prepare_move_line_default_vals(self, write_off_line_vals=None,force_balance=None):
        result = super()._prepare_move_line_default_vals(write_off_line_vals,force_balance)
        if self.manual_currency_rate_active and self.manual_currency_rate > 0:
            for res in result:
                if self.company_id.currency_id.id == self.currency_id.id:
                    amount_currency = res['amount_currency']
                    if res.get('debit'):
                        res['amount_currency'] = amount_currency / self.manual_currency_rate
                        res['debit'] = abs(amount_currency) / self.manual_currency_rate
                    if res.get('credit'):
                        res['amount_currency'] = amount_currency / self.manual_currency_rate
                        res['credit'] =  abs(amount_currency) / self.manual_currency_rate
                else:
                    amount_currency = res['amount_currency']
                    if res.get('debit') > 0:
                        res['amount_currency'] = amount_currency 
                        res['debit'] = abs(amount_currency) / self.manual_currency_rate
                    if res.get('credit') > 0:
                        res['amount_currency'] = amount_currency 
                        res['credit'] = abs(amount_currency) / self.manual_currency_rate
        return result
    
    def write(self,vals):
        result = super().write(vals)
        if vals.get('amount') and vals.get('amount_currency'):
            for record in self:
                record.amount_currency = vals.get('amount')
        return result
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('amount_currency'):
                vals.update({'amount':vals.get('amount_currency')})
            result = super().create(vals_list)
            if vals.get('amount'):
                vals.update({'amount_currency':vals.get('amount')})
                result.sync_amount()
            return result

    @api.onchange('amount_currency')
    def onchange_amount_currency(self):
        for record in self:
            record.amount = record.amount_currency

    def action_post(self):
        ''' draft -> posted '''
        if self.check_active_currency == False : 
            self.move_id.update({'manual_currency_rate_active': self.manual_currency_rate_active,
                'manual_currency_rate':self.manual_currency_rate,})
            self.update({'amount':self.amount_currency})
        self.move_id._post(soft=False)

        self.filtered(
            lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()

    def action_draft(self):
        ''' posted -> draft '''
        if self.check_active_currency == False : 
           self.update({'amount':self.amount_currency})
        self.move_id.button_draft()


    def sync_amount(self):
        for record in self:
            if record.manual_currency_rate_active and record.manual_currency_rate:
                if record.company_id.currency_id.id == record.currency_id.id:
                    if self.check_active_currency == True : 
                       record.amount_currency = record.amount 
                else:
                    record.amount_currency = record.amount
            else:
                record.amount_currency = record.amount