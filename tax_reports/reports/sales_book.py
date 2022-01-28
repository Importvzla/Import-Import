from odoo import api, models
import locale
import json
from odoo.exceptions import ValidationError


class SalesBook(models.AbstractModel):
    _name = 'report.tax_reports.sales_book'
    _description = 'Libro de Ventas'

    @staticmethod
    def rif_format(rif):
        characters = "-./_ "
        for x in range(len(characters)):
            rif = rif.replace(characters[x], "")
        return rif

    @api.model
    def _get_report_values(self, docids, data=None):
        print('funcion para obtener datos del cliente para el reporte')
        locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
        docs = self.env['account.move'].browse(docids[0])
        fiscal_journal_ids = self.env['account.journal'].search([('x_fiscal', '=', True)])
        invoice_ids = self.env['account.move'].search([
            ('id', 'in', docids), ('journal_id', 'in', fiscal_journal_ids.ids),
        ], order="invoice_date ASC")
        # invoice_ids = self.env['account.move'].search([
        #     ('id', 'in', docids), ('journal_id.name', 'in', ['VENTAS FISCALES','RETENCIONES DE IVA']),
        # ], order="invoice_date ASC")

        min_date = invoice_ids[0].invoice_date
        initial_date = min_date.strftime('%m-%Y')
        invoice_number = len(invoice_ids)
        max_date = invoice_ids[invoice_number - 1].invoice_date
        final_date = max_date.strftime('%m-%Y')

        data_sales_book = []
        number = 0

        sum_amount_total = 0.0
        sum_exempt_amount = 0.0
        sum_tax_base_amount = 0.0
        sum_tax_iva_amount = 0.0
        sum_iva_withheld = 0.0

        for invoice in invoice_ids:

            number += 1

            if invoice.x_tipodoc == 'Factura':
                document_type = '01'
                invoice_number = invoice.ref
                debit_note = ''
                credit_note = ''
            elif invoice.x_tipodoc == 'Nota de Crédito':
                document_type = '02'
                invoice_number = ''
                debit_note = ''
                credit_note = invoice.ref
            elif invoice.x_tipodoc == 'Nota de Débito':
                document_type = '03'
                invoice_number = ''
                debit_note = invoice.ref
                credit_note = ''
            else:
                document_type = ''

            if invoice.reversed_entry_id:
                affected_invoice_no = invoice.reversed_entry_id.ref
            else:
                affected_invoice_no = ''

            date = invoice.invoice_date.strftime('%d/%m/%Y')
            #rif_company = self.rif_format(invoice.company_id.vat)
            rif_supplier = self.rif_format(invoice.fiscal_provider.vat)
            customer_name = invoice.fiscal_provider.name
            #fiscal_period = str(invoice.date.year) + str(invoice.date.month)
            # column_4 = 'C'
            #invoice_number = invoice.ref
            control_number = invoice.x_ncontrol
            # debit_note = 'xxxx'
            # credit_note = 'yyyy'
            transaction_type = document_type
            affected_invoice_number = affected_invoice_no
            # amount_total = 0.0
            # exempt_amount = 0.0
            tax_base = 0.0
            # retention_percentage = ''
            tax_iva = 0.0
            iva_withheld = 0.0
            #voucher_number = invoice.x_ncomprobante
            column_17 = '-'

            exempt_sum = 0.0
            percentage = ''

            for ili in invoice.invoice_line_ids:
                for ti in ili.tax_ids:
                    if ti.x_tipoimpuesto == 'IVA':
                        tax_base += ili.price_subtotal
                        line_iva_id = invoice.line_ids.search([('name', '=', ti.name), ('move_id', '=', invoice.id)])
                        if len(line_iva_id) > 1:
                            tax_iva = 0.0
                            for lii in line_iva_id:
                                if invoice.x_tipodoc == 'Nota de Crédito':
                                    tax_iva += lii.debit
                                else:
                                    tax_iva += lii.credit
                        else:
                            if invoice.x_tipodoc == 'Nota de Crédito':
                                tax_iva = line_iva_id.debit
                            else:
                                tax_iva = line_iva_id.credit
                        percentage = line_iva_id[0].name
                    if ti.x_tipoimpuesto == 'EXENTO':
                        exempt_sum += ili.price_subtotal
                    # if ti.x_tipoimpuesto == 'RIVA':
                    #     line_riva_id = invoice.line_ids.search([('name', '=', ti.name), ('move_id', '=', invoice.id)])
                    #     if invoice.x_tipodoc == 'Nota de Crédito':
                    #         iva_withheld = line_riva_id.debit
                    #     else:
                    #         iva_withheld = line_riva_id.credit

            if percentage != '':
                retention_percentage = int(percentage[4:-1])
            else:
                retention_percentage = 0

            if invoice.x_tipodoc == 'Nota de Crédito':
                amount_total = -1 * (tax_iva + tax_base + exempt_sum)
                tax_base_amount = -1 * tax_base
                tax_iva_amount = -1 * tax_iva
                exempt_amount = -1 * exempt_sum
            else:
                amount_total = tax_iva + tax_base + exempt_sum
                tax_base_amount = tax_base
                tax_iva_amount = tax_iva
                exempt_amount = exempt_sum

            # if exempt_sum == 0.0:
            #     exempt_amount = 0.0
            # else:
            #     if invoice.x_tipodoc == 'Nota de Crédito':
            #         exempt_amount = -1 * exempt_sum
            #     else:
            #         exempt_amount = exempt_sum

            if invoice.invoice_payments_widget != 'false':
                res = json.loads(invoice.invoice_payments_widget)
                for apr in res['content']:
                    memo = apr['ref']
                    type_journal = memo[0:3]
                    #account_payment_register = res['content'][0]
                    #memo = account_payment_register['ref']
                    #type_journal = memo[0:3]
                    if type_journal == 'IVA':
                        ref_journal = memo[memo.find('(')+1:-1]
                        account_payment = self.env['account.payment'].search([
                            ('move_id', '=', apr['move_id']),
                            ('ref', '=', ref_journal),
                        ])
                        iva_withheld = account_payment.amount
                        iva_receipt_number = account_payment.ref
                        break
                    else:
                        iva_withheld = 0.0
                        iva_receipt_number = ""
            else:
                iva_withheld = 0.0
                iva_receipt_number = ""

            sum_amount_total += amount_total
            sum_exempt_amount += exempt_amount
            sum_tax_base_amount += tax_base_amount
            sum_tax_iva_amount += tax_iva_amount
            sum_iva_withheld += iva_withheld
            total_tax_base_column = sum_tax_base_amount + sum_exempt_amount

            sales_book_line = {
                'number': number,
                'date': date,
                'rif_supplier': rif_supplier,
                'customer_name': customer_name,
                # 'fiscal_period': fiscal_period,
                'invoice_number': invoice_number,
                'control_number': control_number,
                'debit_note': debit_note,
                'credit_note': credit_note,
                'transaction_type': transaction_type,
                # 'rif_supplier': rif_supplier,
                'affected_invoice_number': affected_invoice_number,
                'amount_total': locale.format_string('%10.2f', amount_total, grouping=True),
                'exempt_amount': locale.format_string('%10.2f', exempt_amount, grouping=True),
                'tax_base': locale.format_string('%10.2f', tax_base_amount, grouping=True),
                'retention_percentage': retention_percentage,
                'tax_iva': locale.format_string('%10.2f', tax_iva_amount, grouping=True),
                'iva_withheld': locale.format_string('%10.2f', iva_withheld, grouping=True),
                # 'voucher_number': voucher_number,
                'iva_receipt_number': iva_receipt_number,
            }
            data_sales_book.append(sales_book_line)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            'data_sales_book': data_sales_book,
            'sum_amount_total': locale.format_string('%10.2f', sum_amount_total, grouping=True),
            'sum_exempt_amount': locale.format_string('%10.2f', sum_exempt_amount, grouping=True),
            'sum_tax_base_amount': locale.format_string('%10.2f', sum_tax_base_amount, grouping=True),
            'sum_tax_iva_amount': locale.format_string('%10.2f', sum_tax_iva_amount, grouping=True),
            'sum_iva_withheld': locale.format_string('%10.2f', sum_iva_withheld, grouping=True),
            'total_tax_base_column': locale.format_string('%10.2f', total_tax_base_column, grouping=True),
            'initial_date': initial_date,
            'final_date': final_date,
            # 'fiscal_period': fiscal_period,
            # 'exempt_sum': locale.format_string('%10.2f', exempt_sum, grouping=True),
            # 'tax_base': locale.format_string('%10.2f', tax_base, grouping=True),
            # 'retention_percentage': retention_percentage,
            # 'tax_iva': locale.format_string('%10.2f', tax_iva, grouping=True),
            # 'iva_withheld': locale.format_string('%10.2f', iva_withheld, grouping=True),
            # 'amount_total': locale.format_string('%10.2f', amount_total, grouping=True),
            # 'transaction_type': transaction_type,
        }
        return docargs
