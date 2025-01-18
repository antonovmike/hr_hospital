import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Person(models.AbstractModel):
    _name = 'hr_hospital.person'
    _description = 'Person'

    name_first = fields.Char()
    name_last = fields.Char()
    phone = fields.Char()
    email = fields.Char()
    photo = fields.Binary()
    gender = fields.Selection([
        ('male', 'Male'), ('female', 'Female'), ('other', 'Undefined')
        ])
