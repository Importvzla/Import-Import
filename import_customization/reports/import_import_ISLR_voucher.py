from odoo import api, models
from odoo.exceptions import ValidationError


class ImportImportIslrVoucher(models.AbstractModel):
    _name = 'report.import_customization.islr_voucher'
    _description = 'Factura fiscal import import pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('funcion para obtener datos del cliente para el reporte')
        docs = self.env['account.move'].browse(docids[0])

        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
        }
        return docargs
