import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Person(models.AbstractModel):
    _name = 'hr.hospital.person'
    _description = 'Person'

    name_first = fields.Char()
    name_last = fields.Char()
    phone = fields.Char()
    email = fields.Char()
    photo = fields.Binary()
    gender = fields.Selection([
        ('male', 'Male'), ('female', 'Female'), ('other', 'Undefined')
        ])

    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('name_first', 'name_last')
    def _compute_display_name(self):
        for record in self:
            if record.name_first and record.name_last:
                record.display_name = f"{record.name_first} {record.name_last}"
            elif record.name_first:
                record.display_name = record.name_first
            elif record.name_last:
                record.display_name = record.name_last
            else:
                record.display_name = "Unnamed"
