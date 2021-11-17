# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
from odoo.exceptions import UserError
from odoo.exceptions import Warning

class account_invoice_line(models.Model):
	_inherit ='account.move.line'


	@api.model
	def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
		''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
		in some business fields (affecting the 'price_subtotal' field).

		:param price_subtotal:  The untaxed amount.
		:param move_type:       The type of the move.
		:param currency:        The line's currency.
		:param company:         The move's company.
		:param date:            The move's date.
		:return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
		'''
		if move_type in self.move_id.get_outbound_types():
			sign = 1
		elif move_type in self.move_id.get_inbound_types():
			sign = -1
		else:
			sign = 1

		amount_currency = price_subtotal * sign
		print("--amount_currency",amount_currency)
		if self.sale_line_ids.order_id.sale_manual_currency_rate_active:
			if self.sale_line_ids.order_id.sale_manual_currency_rate > 0:
				currency_rate = self.company_id.currency_id.rate / self.sale_line_ids.order_id.sale_manual_currency_rate
				balance = amount_currency*currency_rate
			else:
				balance = currency._convert(amount_currency, company.currency_id, company,
											date or fields.Date.context_today(self))
		elif self.purchase_order_id.purchase_manual_currency_rate_active:
			if self.purchase_order_id.purchase_manual_currency_rate > 0:
				currency_rate = self.company_id.currency_id.rate / self.purchase_order_id.purchase_manual_currency_rate
				balance = amount_currency*currency_rate
			else:
				balance = currency._convert(amount_currency, company.currency_id, company,
											date or fields.Date.context_today(self))



		elif self.move_id.manual_currency_rate_active:
			if self.move_id.manual_currency_rate > 0:
				currency_rate = self.company_id.currency_id.rate / self.move_id.manual_currency_rate
				balance = amount_currency*currency_rate
			else:
				balance = currency._convert(amount_currency, company.currency_id, company,
											date or fields.Date.context_today(self))

		else:
			balance = currency._convert(amount_currency, company.currency_id, company,
										date or fields.Date.context_today(self))

		return {
			'amount_currency': amount_currency,
			'currency_id': currency.id,
			'debit': balance > 0.0 and balance or 0.0,
			'credit': balance < 0.0 and -balance or 0.0,
		}


	@api.onchange('amount_currency')
	def _onchange_amount_currency(self):
		for line in self:
			company = line.move_id.company_id
			if line.move_id.manual_currency_rate > 0:
				currency_rate = line.company_id.currency_id.rate / line.move_id.manual_currency_rate
				balance = line.amount_currency*currency_rate
			else:
				balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, line.move_id.date)
			line.debit = balance if balance > 0.0 else 0.0
			line.credit = -balance if balance < 0.0 else 0.0

			if not line.move_id.is_invoice(include_receipts=True):
				continue

			line.update(line._get_fields_onchange_balance())
			line.update(line._get_price_total_and_subtotal())

	@api.onchange('product_id')
	def _onchange_product_id(self):
		for line in self:
			if not line.product_id or line.display_type in ('line_section', 'line_note'):
				continue

			line.name = line._get_computed_name()
			line.account_id = line._get_computed_account()
			line.tax_ids = line._get_computed_taxes()
			line.product_uom_id = line._get_computed_uom()
			line.price_unit = line._get_computed_price_unit()

			# price_unit and taxes may need to be adapted following Fiscal Position
			line._set_price_and_tax_after_fpos()

			# # Convert the unit price to the invoice's currency.
			company = line.move_id.company_id
			
			if line.move_id.manual_currency_rate_active:
				currency_rate = line.move_id.manual_currency_rate/company.currency_id.rate
				if line.move_id.is_sale_document(include_receipts=True):
					price_unit = line.product_id.lst_price
				elif line.move_id.is_purchase_document(include_receipts=True):
					price_unit = line.product_id.standard_price
				else:
					return 0.0
				manual_currency_rate = price_unit * currency_rate
				line.price_unit = manual_currency_rate


class account_invoice(models.Model):
	_inherit ='account.move'

	manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
	manual_currency_rate = fields.Float('Rate', digits=(12, 6))

	@api.constrains("manual_currency_rate")
	def _check_manual_currency_rate(self):
		for record in self:
			if record.manual_currency_rate_active:
				if record.manual_currency_rate == 0:
					raise Warning(_('Exchange Rate Field is required , Please fill that.'))

	@api.onchange('manual_currency_rate_active', 'currency_id')
	def check_currency_id(self):
		if self.manual_currency_rate_active:
			if self.currency_id == self.company_id.currency_id:
				self.manual_currency_rate_active = False
				raise Warning(_('Company currency and invoice currency same, You can not added manual Exchange rate in same currency.'))



class stock_move(models.Model):
	_inherit = 'stock.move'

	def _create_in_svl(self, forced_quantity=None):
		"""Create a `stock.valuation.layer` from `self`.

		:param forced_quantity: under some circunstances, the quantity to value is different than
			the initial demand of the move (Default value = None)
		"""

		rec  = super(stock_move, self)._create_in_svl(forced_quantity=None)
		for rc in rec:
			for line in self:
				if line.purchase_line_id :
					if line.purchase_line_id.order_id.purchase_manual_currency_rate_active:
						price_unit = line.purchase_line_id.order_id.currency_id.round((line.purchase_line_id.price_unit)/line.purchase_line_id.order_id.purchase_manual_currency_rate)

						rc.write({'unit_cost' : price_unit,'value' :price_unit * rc.quantity,'remaining_value' : price_unit * rc.quantity})

		return rec

	def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
		"""
		Generate the account.move.line values to post to track the stock valuation difference due to the
		processing of the given quant.
		"""
		self.ensure_one()

		# the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
		# the company currency... so we need to use round() before creating the accounting entries.
		debit_value = self.company_id.currency_id.round(cost)
		credit_value = debit_value

		valuation_partner_id = self._get_partner_id_for_valuation_lines()

		if self.purchase_line_id.order_id.purchase_manual_currency_rate_active:
			debit_value = self.purchase_line_id.order_id.currency_id.round((self.purchase_line_id.price_unit*qty)/self.purchase_line_id.order_id.purchase_manual_currency_rate)
			credit_value = debit_value

			res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

		else:
			res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

		if self.sale_line_id.order_id.sale_manual_currency_rate:
			debit_value = self.sale_line_id.order_id.currency_id.round((self.sale_line_id.price_unit*qty)/self.sale_line_id.order_id.sale_manual_currency_rate)
			credit_value = debit_value
			res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

		else:
			res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

		return res







# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
