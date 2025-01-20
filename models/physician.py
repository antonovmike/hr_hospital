import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Physician(models.Model):
    _name = 'hr.hospital.physician'
    _inherit = 'hr_hospital.person'
    _description = 'Physician'

    specialty = fields.Char(default='Internal Medicine')
    is_intern = fields.Boolean(string='Is Intern', default=False)
    mentor_id = fields.Many2one(
        'hr.hospital.physician',
        string='Mentor',
        domain=[('is_intern', '=', False)],
        help='Supervising physician for interns'
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
        string='Related User',
        help='The user account linked to this physician'
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
