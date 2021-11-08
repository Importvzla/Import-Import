from odoo import api, models
import locale
from odoo.exceptions import ValidationError


class ImportImportIslrVoucher(models.AbstractModel):
    _name = 'report.import_customization.islr_voucher'
    _description = 'Factura fiscal import import pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('funcion para obtener datos del cliente para el reporte')
        locale.setlocale(locale.LC_ALL, 'es_VE.utf8')
        docs = self.env['account.move'].browse(docids[0])

        data_islr = []
        tax_withheld = 0.0

        # islr_voucher_line = {
        #     'payment_date': docs.invoice_date,
        #     'document_number': docs.ref,
        #     'control_No': docs.x_ncontrol,
        #     'amount_paid': 0.0,
        #     'amount_document': 0.0,
        #     'amount_obt': 0.0,
        #     'retention_percentage': 0.0,
        #     'ret_cod': '',
        #     'description': '',
        #     'tax_withheld_line': 0.0,
        # }

        for ili in docs.invoice_line_ids:
            islr_voucher_line = {
                'payment_date': docs.invoice_date,
                'document_number': docs.ref,
                'control_No': docs.x_ncontrol,
                'amount_paid': '0,0',
                'amount_document': 0.0,
                'amount_obt': 0.0,
                'retention_percentage': 0.0,
                'ret_cod': '',
                'description': '',
                'tax_withheld_line': 0.0,
            }
            for ti in ili.tax_ids:
                if ti.x_tipoimpuesto == 'ISLR':
                    line_id = docs.line_ids.search([('name', '=', ti.name), ('move_id', '=', docs.id)])
                    print(line_id)
                    if docs.x_tipodoc == 'Nota de Crédito':
                        tax_withheld_line = line_id.credit
                        tax_withheld += line_id.credit
                    else:
                        tax_withheld_line = line_id.debit
                        tax_withheld += line_id.debit

                    islr_voucher_line.update(
                        amount_document=locale.format_string('%10.2f', ili.price_subtotal, grouping=True),
                        amount_obt=locale.format_string('%10.2f', ili.price_subtotal, grouping=True),
                        retention_percentage=locale.format_string('%10.2f', ti.amount, grouping=True),
                        ret_cod=ti.name[:6],
                        description=ti.name[7:],
                        tax_withheld_line=locale.format_string('%10.2f', tax_withheld_line, grouping=True),
                    )

                    data_islr.append(islr_voucher_line)
                    break


        if not data_islr:
            islr_voucher_line = {
                'payment_date': docs.invoice_date,
                'document_number': docs.ref,
                'control_No': docs.x_ncontrol,
                'amount_paid': '0,0',
                'amount_document': '0,0',
                'amount_obt': '0,0',
                'retention_percentage': '0,0',
                'ret_cod': '',
                'description': '',
                'tax_withheld_line': '0,0',
            }
            data_islr.append(islr_voucher_line)

        print(data_islr)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            'data_islr': data_islr,
            'tax_withheld': locale.format_string('%10.2f', tax_withheld, grouping=True),
        }
        return docargs
