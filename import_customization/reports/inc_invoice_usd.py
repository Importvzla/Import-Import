from odoo import api, models
import locale
from odoo.exceptions import ValidationError


class ImportInvoice(models.AbstractModel):
    _name = "report.import_customization.inc_usd_invoice"
    _description = "Factura fiscal import import usd pdf"

    @staticmethod
    def description_format(name):
        characters = "]"
        index = name.find(characters)
        if index != -1:
            description = name[index + 1 :]
        else:
            description = name
        return description

    @staticmethod
    def address_format(partner_id):
        street = partner_id.street if partner_id.street else ""
        street2 = partner_id.street2 if partner_id.street2 else ""
        zip_code = partner_id.zip if partner_id.zip else ""
        city = partner_id.city if partner_id.city else ""
        state = partner_id.state_id.name if partner_id.state_id.name else ""
        country = partner_id.country_id.name if partner_id.country_id.name else ""
        address = (
            street
            + " "
            + street2
            + " "
            + city
            + " "
            + state
            + " "
            + zip_code
            + " "
            + country
        )
        return address

    @api.model
    def _get_report_values(self, docids, data=None):
        print("funcion para obtener datos del cliente para el reporte")
        # locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
        docs = self.env["account.move"].browse(docids[0])

        amount_untaxed = 0.0
        exempt_sum = 0.0
        tax_base = 0.0
        tax_iva = 0.0
        discount_sum = 0.0
        overall_weight = 0.0
        purchase_order = ""

        list_name = []

        stock_move_lines = self.env["stock.move.line"].search(
            [("origin", "=", docs.invoice_origin), ("picking_code", "=", "outgoing")]
        )

        lines = []
        lotes = docs._get_invoiced_lot_values()

        for ili in docs.invoice_line_ids:
            if not ili.display_type:
                if stock_move_lines:
                    for sml in stock_move_lines:
                        if sml.product_id == ili.product_id:
                            if sml.reference not in list_name:
                                list_name.append(sml.reference)

                overall_weight += ili.quantity
                unit_price_without_tax = 0.0
                for ti in ili.tax_ids:
                    if ili.discount:
                        discount_sum += round(ili.price_unit * (ili.discount / 100), 2)
                    else:
                        discount_sum += 0.0

                    if ti.x_tipoimpuesto == "IVA":
                        unit_price_without_tax = round(
                            ili.price_unit / ((100 + ti.amount) / 100), 2
                        )
                        tax_base += ili.price_subtotal
                        line_iva_id = docs.line_ids.search(
                            [("name", "=", ti.name), ("move_id", "=", docs.id)]
                        )
                        tax_iva = abs(line_iva_id.amount_currency)
                    else:
                        unit_price_without_tax = ili.price_unit

                    if ti.x_tipoimpuesto == "EXENTO":
                        exempt_sum += ili.price_subtotal
                    if ti.x_tipoimpuesto == "RIVA":
                        line_riva_id = docs.line_ids.search(
                            [("name", "=", ti.name), ("move_id", "=", docs.id)]
                        )
                        if docs.x_tipodoc == "Nota de Crédito":
                            iva_withheld = line_riva_id.debit
                        else:
                            iva_withheld = line_riva_id.credit

                if ili.tax_ids and ili.tax_ids[0].name == "Exento":
                    code = "(E)"
                else:
                    code = "(G)"

                amount_untaxed += unit_price_without_tax

                lote = []
                for lt in lotes:
                    if lt["product_name"] == ili.name:
                        lot = {
                            "name": ("Nro. Lote: " + lt["lot_name"]),
                            "quantity": lt["quantity"][:-4],
                        }
                        lote.append([lot])

            vals = {
                "price_subtotal": locale.format_string(
                    " % 10.2f", ili.price_subtotal, grouping=True
                ),
                "price_total": locale.format_string(
                    "%10.2f", ili.price_total, grouping=True
                ),
                "default_code": ili.product_id.default_code,
                "name": self.description_format(ili.name),
                "lote": lote,
                "product_uom_id": ili.product_uom_id.name,
                "quantity": locale.format_string("%10.2f", ili.quantity, grouping=True),
                "price_unit": locale.format_string(
                    "%10.2f", ili.price_unit, grouping=True
                ),
                "discount": ili.discount,
                "display_type": ili.display_type,
                "code": code,
            }
            lines.append(vals)

            if docs.invoice_origin:
                sale_order_id = self.env["sale.order"].search(
                    [("name", "=", docs.invoice_origin)]
                )
                if sale_order_id:
                    purchase_order = sale_order_id.x_ocompra

        amount_total = tax_iva + tax_base + exempt_sum

        docargs = {
            "doc_ids": docids,
            "doc_model": "account.move",
            "data": data,
            "docs": docs,
            "address": self.address_format(docs.partner_id),
            "billing_address": self.address_format(docs.partner_id),
            "amount_untaxed": locale.format_string(
                "%10.2f", docs.amount_untaxed, grouping=True
            ),
            "overall_weight": locale.format_string(
                "%10.2f", overall_weight, grouping=True
            ),
            "discount_sum": locale.format_string("%10.2f", discount_sum, grouping=True),
            "tax_iva": tax_iva,
            "exempt_sum": exempt_sum,
            "amount_total": amount_total,
            "tax_base": tax_base,
            "lines": lines,
            "purchase_order": purchase_order,
            "delivery_note": ", ".join(list_name),
        }
        return docargs
