from odoo import api, models
import locale
from odoo.exceptions import ValidationError


class IvaTxt(models.AbstractModel):
    _name = 'report.tax_reports.iva_txt'
    _description = 'txt de los comprobante de retencion de iva pdf'

    @staticmethod
    def rif_format(rif):
        characters = "-./_"
        for x in range(len(characters)):
            rif = rif.replace(characters[x], "")
        return rif

    @api.model
    def _get_report_values(self, docids, data=None):
        print('funcion para obtener datos del cliente para el reporte')
        locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
        docs = self.env['account.move'].browse(docids[0])
        invoice_ids = self.env['account.move'].search([
            ('id', 'in', docids), ('x_ncomprobante', '!=', False)
        ])
        data_txt_iva = []

        for invoice in invoice_ids:

            if invoice.x_tipodoc == 'Factura':
                document_type = '01'
            elif invoice.x_tipodoc == 'Nota de Crédito':
                document_type = '02'
            elif invoice.x_tipodoc == 'Nota de Débito':
                document_type = '03'
            else:
                document_type = ''

            if invoice.reversed_entry_id:
                affected_invoice_no = invoice.reversed_entry_id.name
            else:
                affected_invoice_no = 0

            rif_company = self.rif_format(invoice.company_id.vat)
            fiscal_period = str(invoice.date.year) + str(invoice.date.month)
            date = invoice.invoice_date
            column_4 = 'C'
            transaction_type = document_type
            rif_supplier = self.rif_format(invoice.fiscal_provider.vat)
            invoice_number = invoice.ref
            control_number = invoice.x_ncontrol
            # amount_total = 0.0
            tax_base = 0.0
            iva_withheld = 0.0
            affected_invoice_number = affected_invoice_no
            voucher_number = invoice.x_ncomprobante #todo campo 13 agregar el xml
            # exempt_amount = 0.0
            # retention_percentage = ''
            column_16 = '0'

            exempt_sum = 0.0
            percentage = ''
            tax_iva = 0.0

            for ili in invoice.invoice_line_ids:
                for ti in ili.tax_ids:
                    if ti.x_tipoimpuesto == 'IVA':
                        tax_base += ili.price_subtotal
                        line_iva_id = invoice.line_ids.search([('name', '=', ti.name), ('move_id', '=', invoice.id)])
                        if invoice.x_tipodoc == 'Nota de Crédito':
                            tax_iva = line_iva_id.credit
                        else:
                            tax_iva = line_iva_id.debit
                        percentage = line_iva_id.name
                    if ti.x_tipoimpuesto == 'EXENTO':
                        exempt_sum += ili.price_subtotal
                    if ti.x_tipoimpuesto == 'RIVA':
                        line_riva_id = invoice.line_ids.search([('name', '=', ti.name), ('move_id', '=', invoice.id)])
                        if invoice.x_tipodoc == 'Nota de Crédito':
                            iva_withheld = line_riva_id.debit
                        else:
                            iva_withheld = line_riva_id.credit

            if percentage != '':
                retention_percentage = float(percentage[4:-1])
            else:
                retention_percentage = 0.0

            amount_total = tax_iva + tax_base + exempt_sum
            exempt_amount = exempt_sum


            iva_txt_line = {
                'rif_company': rif_company,
                'fiscal_period': fiscal_period,
                'date': date,
                'column_4': column_4,
                'transaction_type': transaction_type,
                'rif_supplier': rif_supplier,
                'invoice_number': invoice_number,
                'control_number': control_number,
                'amount_total': amount_total,
                'tax_base': tax_base,
                'iva_withheld': iva_withheld,
                'affected_invoice_number': affected_invoice_number,
                'voucher_number': voucher_number,
                'exempt_amount': exempt_amount,
                'retention_percentage': retention_percentage,
                'column_16': column_16,
            }
            data_txt_iva.append(iva_txt_line)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            'data_txt_iva': data_txt_iva,
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
