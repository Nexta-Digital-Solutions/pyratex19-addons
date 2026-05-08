
from odoo import api, fields, models, _

class ProductTemplateAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    colorgroup_id = fields.Many2many('color.group',compute='_compute_group_id', store=True, readonly=True, string='Group')

    @api.depends('value_ids')
    def _compute_group_id(self):
        for line in self:
            groups = line.value_ids.mapped('colorgroup_id')
            line.update({'colorgroup_id': groups})


