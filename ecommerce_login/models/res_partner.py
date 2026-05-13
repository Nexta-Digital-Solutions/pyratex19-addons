from odoo import fields, models, api, _
from docx import Document
from docx.shared import Mm
from docxtpl import DocxTemplate,InlineImage
import jinja2
import tempfile
from PyPDF2 import PdfFileMerger
from odoo.exceptions import UserError
import io
import os
import base64
from PIL import Image
from io import StringIO
import re
from binascii import a2b_base64


class ResPartner(models.Model):
    _inherit = 'res.partner'

    profession = fields.Selection([('individual', 'An Individual'), ('student', 'A Student'), ('company', 'A Company'), ('library','A Material Library'), ('project','Starting a new project')], string='Profession')
    about_us = fields.Selection([('engine', 'Search engine'), ('instagram', 'Instagram'), ('linkedin', 'Linkedin'), ('word','Word of Mouth'), ('events','Events'), ('newspaper', 'Newspaper/ Press'),('other','Other')], string='About Us')


    def generateTempFile(self, suffix = ''):
        tf = tempfile.NamedTemporaryFile(mode='w+', delete=True, suffix=suffix)
        
        temp_file_name = tf.name
        folder = tempfile.gettempdir()
        tf.close()
        return { 'name': temp_file_name, 'folder': folder }  
   
    def createDocumentSignature(self,signature):
        temp_file = self.generateTempFile('.jpg')
        imgstr = re.search(r'base64,(.*)', signature).group(1)
        binary_data = a2b_base64(imgstr)
        Out = open(temp_file.get('name'), 'wb')
        Out.write(binary_data)
        Out.close()
        return temp_file
    
    def createDocumentMDNA(self, partner_id, data, signature):
        folder = 'mldna'
        template_name = "mldna.docx"
        folder_template_id =  self.env['documents.folder'].sudo().search([ ('name', '=', 'templates')])
        folder_id = self.env['documents.folder'].sudo().search([ ('name', '=', folder)])
        docs = self.env['documents.document'].sudo().search( [('folder_id', '=', folder_template_id.id), ('name', '=', template_name)], limit = 1)
        
        if (not docs):
            return
        
        merger = PdfFileMerger()
        signature_file = self.createDocumentSignature(signature)
        for doc in docs:
            output = io.BytesIO()
            output.write(doc.raw)
            output.seek(0)

            temp_file = self.generateTempFile()
                       
            temp_file_name = temp_file.get('name')
			
            outfile = open(temp_file_name, "wb+")
            outfile.write(output.getbuffer())
            outfile.close()
			
            dic = {
             'name'   : data['data[name]'],
             'lastname': data['data[lastname]'],
             'address1': ' '.join({ data['data[address1]'], data['data[address2]'] }),
             'postalcode': data['data[postalcode]'],
            }
            
            template_render = self.template_renderer(temp_file, dic, signature_file)
            temp_file_name_pdf = template_render['name'] + ".pdf"

            os_cmd = os.system("soffice --headless --convert-to pdf --outdir %s %s" % (template_render['folder'], template_render['name']) )
            merger.append(temp_file_name_pdf, import_bookmarks=False)
            
        myio = io.BytesIO()
        merger.write(myio)
        merger.close()
        myio.seek(0)
        
        byte_str = myio.read()
        fileAscii = base64.b64encode(byte_str).decode('ASCII')
        return self.env['documents.document'].sudo().create ({
            'name': 'mdna.pdf',
            'partner_id': partner_id.id,
            'datas': fileAscii,
            'type': 'binary',
            'mimetype': 'application/pdf',
            'folder_id': folder_id.id
        })
    
    def template_renderer(self, docTemplate, dataTemplate, signature_file, field_not_found = False):
        docTemplate_new =self.generateTempFile()
        jinja_env = jinja2.Environment(autoescape=True)
        tpl = DocxTemplate(docTemplate['name'])
        dataTemplate['signature'] =  InlineImage(tpl,  signature_file.get('name'), width=Mm(30), height=Mm(20))
        try:
            tpl.render(dataTemplate, jinja_env)
            tpl.save(docTemplate_new['name'])
        except Exception as e:
            new_field = e.message.split(' ')[0].replace("'","")
            if (field_not_found == new_field):
                raise UserError (_("Campo %s no encontrado" % ( new_field )))
        return docTemplate_new