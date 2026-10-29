# -*- coding: utf-8 -*-
import base64
import logging
import os
import re
import shutil
import subprocess
import tempfile
from binascii import a2b_base64

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MNDA_TEMPLATE_FOLDER = 'templates'
MNDA_TEMPLATE_NAME = 'mldna.docx'
MNDA_OUTPUT_FOLDER = 'mldna'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    profession = fields.Selection([('individual', 'An Individual'), ('student', 'A Student'), ('company', 'A Company'), ('library', 'A Material Library'), ('project', 'Starting a new project')], string='Profession')
    about_us = fields.Selection([('engine', 'Search engine'), ('instagram', 'Instagram'), ('linkedin', 'Linkedin'), ('word', 'Word of Mouth'), ('events', 'Events'), ('newspaper', 'Newspaper/ Press'), ('other', 'Other')], string='About Us')

    # ------------------------------------------------------------------
    # MNDA firmado (Odoo 19)
    #
    # - Las carpetas de Documentos son ahora registros documents.document de
    #   tipo 'folder' (documents.folder ya no existe).
    # - Ya no hace falta PdfFileMerger (no existe en las versiones actuales de
    #   PyPDF2/pypdf): solo hay un documento y se guarda el PDF de LibreOffice.
    # ------------------------------------------------------------------

    def _get_mnda_folders(self):
        Documents = self.env['documents.document'].sudo()
        template_folder = Documents.search(
            [('type', '=', 'folder'), ('name', '=', MNDA_TEMPLATE_FOLDER)], limit=1)
        output_folder = Documents.search(
            [('type', '=', 'folder'), ('name', '=', MNDA_OUTPUT_FOLDER)], limit=1)
        return template_folder, output_folder

    def createDocumentMDNA(self, partner_id, data, signature):
        """Genera el PDF del MNDA firmado a partir de la plantilla Word
        'templates/mldna.docx' de Documentos y lo guarda en la carpeta 'mldna'.

        :param partner_id: contacto (res.partner) que firma
        :param data: datos del formulario, sin el prefijo data[...]
        :param signature: firma como data URL (image/png;base64,...)
        """
        Documents = self.env['documents.document'].sudo()
        template_folder, output_folder = self._get_mnda_folders()
        template_doc = Documents.search([
            ('folder_id', '=', template_folder.id),
            ('name', '=', MNDA_TEMPLATE_NAME),
            ('type', '=', 'binary'),
        ], limit=1) if template_folder else Documents
        if not template_doc or not template_doc.raw:
            _logger.warning("MNDA: template %s/%s not found in Documents",
                            MNDA_TEMPLATE_FOLDER, MNDA_TEMPLATE_NAME)
            return False

        workdir = tempfile.mkdtemp(prefix='mnda_')
        try:
            template_path = os.path.join(workdir, 'template.docx')
            with open(template_path, 'wb') as f:
                f.write(template_doc.raw)
            signature_path = self.createDocumentSignature(signature, workdir)

            full_name = ' '.join(filter(None, [data.get('name'), data.get('lastname')]))
            values = {
                'name': full_name,
                'firstname': data.get('name') or '',
                'lastname': data.get('lastname') or '',
                'position': data.get('position') or '',
                'company': data.get('company') or '',
                'address1': ' '.join(filter(None, [data.get('address1'), data.get('address2')])),
                'postalcode': data.get('postalcode') or '',
                'city': data.get('city') or '',
                'date': fields.Date.context_today(self).strftime('%d/%m/%Y'),
            }
            rendered_path = os.path.join(workdir, 'mnda.docx')
            self.template_renderer(template_path, rendered_path, values, signature_path)
            pdf_content = self._convert_docx_to_pdf(rendered_path, workdir)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

        values = {
            'name': 'mdna.pdf',
            'partner_id': partner_id.id,
            'datas': base64.b64encode(pdf_content),
            'type': 'binary',
            'mimetype': 'application/pdf',
            'folder_id': output_folder.id if output_folder else False,
        }
        if output_folder and output_folder.owner_id:
            values['owner_id'] = output_folder.owner_id.id
        return Documents.create(values)

    def createDocumentSignature(self, signature, workdir):
        """Guarda la firma (data URL) como imagen y devuelve su ruta."""
        match = re.search(r'base64,(.*)', signature or '')
        if not match:
            raise UserError(_("The signature is missing."))
        signature_path = os.path.join(workdir, 'signature.png')
        with open(signature_path, 'wb') as f:
            f.write(a2b_base64(match.group(1)))
        return signature_path

    def template_renderer(self, template_path, output_path, values, signature_path):
        """Rellena la plantilla Word (docxtpl) con los datos y la firma."""
        import jinja2
        from docx.shared import Mm
        from docxtpl import DocxTemplate, InlineImage

        tpl = DocxTemplate(template_path)
        values = dict(values, signature=InlineImage(tpl, signature_path, width=Mm(30), height=Mm(20)))
        tpl.render(values, jinja2.Environment(autoescape=True))
        tpl.save(output_path)
        return output_path

    def _convert_docx_to_pdf(self, docx_path, workdir):
        """Convierte el Word a PDF con LibreOffice (soffice) y devuelve el contenido."""
        try:
            subprocess.run(
                ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', workdir, docx_path],
                check=True, capture_output=True, timeout=120,
            )
        except (OSError, subprocess.SubprocessError) as e:
            raise UserError(_("Could not convert the MNDA to PDF (LibreOffice): %s", e)) from e
        pdf_path = os.path.splitext(docx_path)[0] + '.pdf'
        with open(pdf_path, 'rb') as f:
            return f.read()
