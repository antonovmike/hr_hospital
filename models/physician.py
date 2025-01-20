import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Physician(models.Model):
    _name = 'hr.hospital.physician'
    _inherit = 'hr_hospital.person'
    _description = 'Physician'

    name = fields.Char(required=True)
    specialty = fields.Char(default='Internal Medicine')
    is_intern = fields.Boolean(string='Is Intern')
    mentor_id = fields.Many2one(
        'hr.hospital.physician',
        string='Mentor',
        domain=[('is_intern', '=', False)]
    )
    intern_ids = fields.One2many(
        'hr.hospital.physician',
        'mentor_id',
        string='Interns',
        help='List of interns under supervision'
    )
    patient_ids = fields.Many2many(
        comodel_name='hr.hospital.patient',
    )
    user_id = fields.Many2one(
        'res.users',
        string='Related User'
    )

    @api.constrains('is_intern', 'mentor_id', 'intern_ids')
    def _check_intern_mentor_constraints(self):
        for physician in self:
            if physician.is_intern and not physician.mentor_id:
                raise ValidationError('Interns must have a mentor assigned')
            if physician.intern_ids and physician.is_intern:
                raise ValidationError('Interns cannot be mentors to other physicians')
            if physician.mentor_id and physician.mentor_id.is_intern:
                raise ValidationError('An intern cannot be assigned as a mentor')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.is_intern:
                self.env['hr.hospital.physician.schedule'].generate_slots_for_physician(
                    record.id
                )
        return records

    def generate_schedule_slots(self):
        """Action to generate schedule slots for the physician."""
        self.ensure_one()
        if self.is_intern:
            raise ValidationError("Cannot generate schedule slots for interns")
        self.env['hr.hospital.physician.schedule'].generate_slots_for_physician(
            self.id
        )
