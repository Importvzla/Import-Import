from odoo import api, models
import locale
from odoo.exceptions import ValidationError


class IvaVoucher(models.AbstractModel):
    _name = 'report.tax_reports.iva_voucher'
    _description = 'comprobante de retencion de iva pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('funcion para obtener datos del cliente para el reporte')
        locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
        docs = self.env['account.move'].browse(docids[0])

        fiscal_period = str(docs.date.month) + "-" + str(docs.date.year)
        print(fiscal_period)

        exempt_sum = 0.0
        tax_base = 0.0
        percentage = ''
        tax_iva = 0.0
        iva_withheld = 0.0
        #amount_total = 0.0

        for ili in docs.invoice_line_ids:
            for ti in ili.tax_ids:
                if ti.x_tipoimpuesto == 'IVA':
                    tax_base += ili.price_subtotal
                    line_iva_id = docs.line_ids.search([('name', '=', ti.name), ('move_id', '=', docs.id)])
                    if docs.x_tipodoc == 'Nota de Crédito':
                        tax_iva = line_iva_id.credit
                    else:
                        tax_iva = line_iva_id.debit
                    percentage = line_iva_id.name
                if ti.x_tipoimpuesto == 'EXENTO':
                    exempt_sum += ili.price_subtotal
                if ti.x_tipoimpuesto == 'RIVA':
                    line_riva_id = docs.line_ids.search([('name', '=', ti.name), ('move_id', '=', docs.id)])
                    if docs.x_tipodoc == 'Nota de Crédito':
                        iva_withheld = line_riva_id.debit
                    else:
                        iva_withheld = line_riva_id.credit

        amount_total = tax_iva + tax_base + exempt_sum

        if percentage != '':
            retention_percentage = percentage[4:]
        else:
            retention_percentage = ''

        if docs.x_tipodoc == 'Factura':
            transaction_type = '01'
        elif docs.x_tipodoc == 'Nota de Crédito':
            transaction_type = '02'
        elif docs.x_tipodoc == 'Nota de Débito':
            transaction_type = '03'
        else:
            transaction_type = ''


        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            'fiscal_period': fiscal_period,
            'exempt_sum': locale.format_string('%10.2f', exempt_sum, grouping=True),
            'tax_base': locale.format_string('%10.2f', tax_base, grouping=True),
            'retention_percentage': retention_percentage,
            'tax_iva': locale.format_string('%10.2f', tax_iva, grouping=True),
            'iva_withheld': locale.format_string('%10.2f', iva_withheld, grouping=True),
            'amount_total': locale.format_string('%10.2f', amount_total, grouping=True),
            'transaction_type': transaction_type,
        }
        return docargs
