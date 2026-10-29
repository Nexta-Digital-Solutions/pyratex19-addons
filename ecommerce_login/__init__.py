# -*- coding: utf-8 -*-

import base64
import os

from . import controllers
from . import models


def post_init_hook(env):
    """Crea en Documentos las carpetas 'templates' y 'mldna' y sube la plantilla
    del MNDA (templates/mldna.docx) si todavía no existen.
    Odoo 19: las carpetas son documents.document de tipo 'folder'."""
    Documents = env['documents.document'].sudo()

    def get_or_create_folder(name):
        folder = Documents.search([('type', '=', 'folder'), ('name', '=', name)], limit=1)
        return folder or Documents.create({'name': name, 'type': 'folder'})

    template_folder = get_or_create_folder('templates')
    get_or_create_folder('mldna')

    template_name = 'mldna.docx'
    if not Documents.search([('folder_id', '=', template_folder.id), ('name', '=', template_name)], limit=1):
        path = os.path.join(os.path.dirname(__file__), 'templates', template_name)
        with open(path, 'rb') as f:
            content = f.read()
        Documents.create({
            'name': template_name,
            'datas': base64.b64encode(content),
            'type': 'binary',
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'folder_id': template_folder.id,
        })
