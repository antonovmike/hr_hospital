import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class DiseaseCategory(models.Model):
    _name = 'hr.hospital.disease.category'
    _description = 'Disease Category'

    name = fields.Char(string='Category Name', required=True)
    disease_ids = fields.One2many(
        'hr.hospital.disease',
        'category_id',
        string='Diseases'
        )


class Disease(models.Model):
    _name = 'hr.hospital.disease'
    _description = 'Disease'

    name = fields.Char(string='Disease Name', required=True)
    category_id = fields.Many2one(
        'hr.hospital.disease.category',
        string='Disease Category',
        required=True
        )
