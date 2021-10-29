from odoo import api, models
from odoo.exceptions import ValidationError


#class TaxBill(models.TransientModel):
class ImportImportBill(models.AbstractModel):
    _name = 'report.import_customization.custom_invoice'
    _description = 'Factura fiscal import import pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('funcion para obtener datos del cliente para el reporte')
        docs = self.env['account.move'].browse(docids[0])
        # move_line = self.env['stock.move.line'].search([
        #         ('result_package_id', '=', docs.id),
        #     ])
        # if move_line:
        #     sale_order = self.env['sale.order'].search([('name', '=', move_line[0].origin)])
        #     partner = sale_order.mapped('partner_shipping_id')
        #     data_client = []
        #     if partner.name:
        #         data_client.append(partner.name)
        #     if partner.vat:
        #         data_client.append(partner.vat)
        #     if partner.street:
        #         data_client.append(partner.street)
        #     if partner.street2:
        #         data_client.append(partner.street2)
        #     if partner.city and partner.zip:
        #         data_client.append(str(partner.city) + ' ' + str(partner.zip))
        #     if partner.country_id.name:
        #         data_client.append(partner.country_id.name)
        #     if partner.phone:
        #         data_client.append(partner.phone)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
        }
        return docargs
