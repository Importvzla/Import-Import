from odoo import api, models
from odoo.exceptions import ValidationError


class ImportImportIslrVoucher(models.AbstractModel):
    _name = 'report.import_customization.iva_voucher'
    _description = 'comprobante de retencion de iva import import pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('funcion para obtener datos del cliente para el reporte')
        docs = self.env['account.move'].browse(docids[0])

        fiscal_period = str(docs.invoice_date.month) + "-" + str(docs.invoice_date.year)
        print(fiscal_period)

        exempt_sum = 0.0
        tax_base = 0.0
        percentage = ''
        tax_iva = 0.0
        iva_withheld = 0.0
        amount_total = docs.amount_total

        for ili in docs.invoice_line_ids:
            for ti in ili.tax_ids:
                if ti.x_tipoimpuesto == 'IVA':
                    tax_base += ili.price_subtotal
                    line_iva_id = docs.line_ids.search([('name', '=', ti.name), ('move_id', '=', docs.id)])
                    tax_iva = line_iva_id.debit
                    percentage = line_iva_id.name
                if ti.x_tipoimpuesto == 'EXENTO':
                    exempt_sum += ili.price_subtotal
                if ti.x_tipoimpuesto == 'RIVA':
                    line_riva_id = docs.line_ids.search([('name', '=', ti.name), ('move_id', '=', docs.id)])
                    iva_withheld = line_riva_id.credit

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
            'exempt_sum': str(exempt_sum).replace('.', ','),
            'tax_base': str(tax_base).replace('.', ','),
            'retention_percentage': retention_percentage,
            'tax_iva': str(tax_iva).replace('.', ','),
            'iva_withheld': str(iva_withheld).replace('.', ','),
            'amount_total': str(amount_total).replace('.', ','),
            'transaction_type': transaction_type,
            # 'data_islr': data_islr,
            # 'tax_withheld': tax_withheld,
        }
        return docargs
