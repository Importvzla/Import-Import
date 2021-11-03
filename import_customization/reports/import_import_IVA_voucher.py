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
        retention_percentage = ''
        tax_iva = 0.0
        iva_withheld = 0.0

        for ili in docs.invoice_line_ids:
            for ti in ili.tax_ids:
                if ti.x_tipoimpuesto == 'IVA':
                    tax_base += ili.price_subtotal
                    line_iva_id = docs.line_ids.search([('name', '=', ti.name), ('move_id', '=', docs.id)])
                    tax_iva = line_iva_id.debit
                    retention_percentage = line_iva_id.name
                if ti.x_tipoimpuesto == 'EXENTO':
                    exempt_sum += ili.price_subtotal
                if  ti.x_tipoimpuesto == 'RIVA':
                    line_riva_id = docs.line_ids.search([('name', '=', ti.name), ('move_id', '=', docs.id)])
                    iva_withheld = line_riva_id.credit


        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            'fiscal_period': fiscal_period,
            'exempt_sum': exempt_sum,
            'tax_base': tax_base,
            'retention_percentage': retention_percentage,
            'tax_iva': tax_iva,
            'iva_withheld': iva_withheld,
            # 'data_islr': data_islr,
            # 'tax_withheld': tax_withheld,
        }
        return docargs
