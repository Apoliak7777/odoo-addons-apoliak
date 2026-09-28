# -*- coding: utf-8 -*-
import base64
import logging
import urllib.request
import xml.etree.ElementTree as ET
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PACKETA_REST_URL = "https://www.zasilkovna.cz/api/rest"


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    packeta_point_id = fields.Char(
        string="Packeta Výdajné miesto / Dopravca ID",
        default="106",
        help="ID výdajného miesta, Z-BOXu alebo 106/131 pre doručenie na adresu.")
    packeta_point_name = fields.Char(
        string="Názov výdajného miesta / Z-BOX")
    packeta_cod_amount = fields.Float(
        string="Suma dobierky (COD)",
        default=0.0,
        help="Ak je zásielka na dobierku, zadajte sumu. 0 = bez dobierky.")
    packeta_weight = fields.Float(
        string="Hmotnosť balíka (kg)",
        default=1.0)
    packeta_packet_id = fields.Char(
        string="Packeta Číslo zásielky",
        readonly=True,
        copy=False)
    packeta_barcode = fields.Char(
        string="Packeta Čiarový kód (Z...)",
        readonly=True,
        copy=False)
    packeta_label_pdf = fields.Binary(
        string="Packeta PDF Štítok",
        readonly=True,
        copy=False)
    packeta_label_filename = fields.Char(
        string="Názov štítku",
        readonly=True,
        copy=False)

    def action_send_to_packeta(self):
        """Odošle zásielku do API Packety (createPacket) a stiahne PDF štítok (packetLabelPdf)."""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        api_pw = (ICP.get_param('apoliak_packeta_connector.api_password') or '').strip()
        eshop = (ICP.get_param('apoliak_packeta_connector.eshop_sender') or 'eshop').strip()
        label_fmt = ICP.get_param('apoliak_packeta_connector.label_format', 'A6 on A6')

        if not api_pw:
            raise UserError(_("Nie je nastavené Packeta API heslo. Nastavte ho v Sklad -> Konfigurácia -> Nastavenia -> Packeta Connector."))

        partner = self.partner_id
        if not partner:
            raise UserError(_("Dodací list nemá priradeného príjemcu (Partner)."))

        full_name = (partner.name or 'Zákazník').strip().split(' ', 1)
        first_name = full_name[0]
        last_name = full_name[1] if len(full_name) > 1 else first_name

        value_amount = self.sale_id.amount_total if self.sale_id and self.sale_id.amount_total > 0 else (self.packeta_cod_amount or 25.0)
        currency = self.sale_id.currency_id.name if self.sale_id and self.sale_id.currency_id else 'EUR'

        # 1. XML createPacket
        root = ET.Element('createPacket')
        ET.SubElement(root, 'apiPassword').text = api_pw
        attrs = ET.SubElement(root, 'packetAttributes')
        ET.SubElement(attrs, 'number').text = self.name or str(self.id)
        ET.SubElement(attrs, 'name').text = first_name
        ET.SubElement(attrs, 'surname').text = last_name
        ET.SubElement(attrs, 'email').text = partner.email or 'info@apoliak.online'
        ET.SubElement(attrs, 'phone').text = partner.phone or partner.mobile or '+421900000000'
        ET.SubElement(attrs, 'addressId').text = str(self.packeta_point_id or '106')
        ET.SubElement(attrs, 'value').text = f"{value_amount:.2f}"
        ET.SubElement(attrs, 'cod').text = f"{self.packeta_cod_amount:.2f}"
        ET.SubElement(attrs, 'currency').text = currency
        ET.SubElement(attrs, 'weight').text = f"{max(self.packeta_weight, 0.1):.2f}"
        ET.SubElement(attrs, 'eshop').text = eshop
        if partner.street:
            ET.SubElement(attrs, 'street').text = partner.street
        if partner.city:
            ET.SubElement(attrs, 'city').text = partner.city
        if partner.zip:
            ET.SubElement(attrs, 'zip').text = partner.zip

        xml_payload = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        req = urllib.request.Request(PACKETA_REST_URL, data=xml_payload, headers={'Content-Type': 'text/xml'})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                resp_xml = ET.fromstring(resp.read())
        except Exception as e:
            raise UserError(_("Chyba komunikácie s Packeta API: %s") % str(e))

        status = resp_xml.findtext('status')
        if status != 'ok':
            fault = resp_xml.findtext('fault') or ''
            string_err = resp_xml.findtext('string') or ''
            detail_err = ET.tostring(resp_xml, encoding='unicode')
            raise UserError(_("Packeta API vrátila chybu (%s): %s\n%s") % (fault, string_err, detail_err))

        packet_id = resp_xml.findtext('./result/id')
        barcode = resp_xml.findtext('./result/barcode') or f"Z{packet_id}"

        # 2. Stiahnutie PDF štítku (packetLabelPdf)
        label_root = ET.Element('packetLabelPdf')
        ET.SubElement(label_root, 'apiPassword').text = api_pw
        ET.SubElement(label_root, 'packetId').text = packet_id
        ET.SubElement(label_root, 'format').text = label_fmt
        ET.SubElement(label_root, 'offset').text = '0'

        label_req = urllib.request.Request(
            PACKETA_REST_URL,
            data=ET.tostring(label_root, encoding='utf-8', xml_declaration=True),
            headers={'Content-Type': 'text/xml'}
        )
        pdf_b64 = False
        try:
            with urllib.request.urlopen(label_req, timeout=20) as l_resp:
                l_xml = ET.fromstring(l_resp.read())
                if l_xml.findtext('status') == 'ok':
                    pdf_b64 = (l_xml.findtext('result') or '').strip()
        except Exception as e:
            _logger.warning("Nepodarilo sa stiahnuť PDF štítok z Packety: %s", e)

        fname = f"Packeta_{barcode}.pdf"
        self.write({
            'packeta_packet_id': packet_id,
            'packeta_barcode': barcode,
            'carrier_tracking_ref': barcode if 'carrier_tracking_ref' in self._fields else False,
            'packeta_label_pdf': pdf_b64,
            'packeta_label_filename': fname,
        })

        self.message_post(
            body=_("<b>📦 Zásielka úspešne zaregistrovaná v Packete!</b><br/>Číslo zásielky: <b>%s</b>") % barcode
        )
        return True
