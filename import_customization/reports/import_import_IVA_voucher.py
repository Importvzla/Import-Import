from odoo import api, models
from odoo.exceptions import ValidationError


class ImportImportIslrVoucher(models.AbstractModel):
    _name = 'report.import_customization.iva_voucher'
    _description = 'comprobante de retencion de iva import import pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('funcion para obtener datos del cliente para el reporte')
        docs = self.env['account.move'].browse(docids[0])

        # data_islr = []
        # tax_withheld = 0.0
        #
        # islr_voucher_line = {
        #     'payment_date': docs.invoice_date,
        #     'document_number': docs.ref,
        #     'control_No': docs.x_studio_nro_control,
        #     'amount_paid': 0.0,
        #     'amount_document': 0.0,
        #     'amount_obt': 0.0,
        #     'retention_percentage': 0.0,
        #     'ret_cod': '',
        #     'description': '',
        #     'tax_withheld': 0.0,
        # }
        #
        #
        # for ili in docs.invoice_line_ids:
        #     for ti in ili.tax_ids:
        #         if ti.x_tipoimpuesto == 'ISLR':
        #             line_id = docs.line_ids.search([('name', '=', ti.name), ('move_id', '=', docs.id)])
        #             print(line_id)
        #             islr_voucher_line.update(
        #                 amount_document=ili.price_subtotal,
        #                 amount_obt=ili.price_subtotal,
        #                 retention_percentage=ti.amount,
        #                 ret_cod=ti.name[:6],
        #                 description=ti.name[7:],
        #                 tax_withheld=line_id.debit,
        #             )
        #             data_islr.append(islr_voucher_line)
        #             tax_withheld += line_id.debit
        #
        # if not data_islr:
        #     data_islr.append(islr_voucher_line)
        #
        # print(data_islr)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            # 'data_islr': data_islr,
            # 'tax_withheld': tax_withheld,
        }
        return docargs
