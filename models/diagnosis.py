import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Diagnosis(models.Model):
    _name = 'hr.hospital.diagnosis'
    _description = 'Diagnosis'

    date_of_diagnosis = fields.Date(required=True)
    physician = fields.Many2one(
        comodel_name='hr.hospital.physician',
        required=True
    )
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        required=True
    )
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        required=True
    )
    treatment_recommendations = fields.Text(required=True)
    
    needs_mentor_review = fields.Boolean(
        string='Needs Mentor Review',
        compute='_compute_needs_mentor_review',
        store=True
    )
    mentor_comment = fields.Text(
        string='Mentor Comment',
        help='Required comment from the mentor for diagnoses made by interns'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_review', 'Pending Mentor Review'),
        ('reviewed', 'Reviewed'),
        ('final', 'Final')
    ], string='Status', default='draft', required=True)

    @api.depends('physician', 'physician.is_intern')
    def _compute_needs_mentor_review(self):
        for record in self:
            record.needs_mentor_review = record.physician.is_intern

    @api.constrains('treatment_recommendations')
    def _check_treatment_recommendations(self):
        for record in self:
            if not record.treatment_recommendations or not record.treatment_recommendations.strip():
                raise ValidationError('Treatment recommendations cannot be empty')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.physician.is_intern:
                record.state = 'draft'
            else:
                record.state = 'final'
        return records

    def action_submit_for_review(self):
        for record in self:
            if not record.physician.is_intern:
                raise ValidationError('Only diagnoses by interns need mentor review')
            record.state = 'pending_review'

    def action_review(self):
        for record in self:
            # Only check for physician link during review
            if record.state == 'pending_review':
                # Get the physician record associated with the current user
                reviewer_physician = self.env['hr.hospital.physician'].search([('user_id', '=', self.env.user.id)], limit=1)
                if not reviewer_physician:
                    raise ValidationError('Current user is not linked to any physician')
                if reviewer_physician.id != record.physician.mentor_id.id:
                    raise ValidationError('Only the assigned mentor can review this diagnosis')
                if not record.mentor_comment:
                    raise ValidationError('Mentor comment is required for review')
                # Update state to reviewed after all validations pass
                record.state = 'reviewed'

    def action_finalize(self):
        for record in self:
            if record.physician.is_intern and not record.mentor_comment:
                raise ValidationError('Mentor comment is required before finalizing an intern diagnosis')
            record.state = 'final'

    @api.constrains('state', 'mentor_comment', 'physician')
    def _check_mentor_comment(self):
        for record in self:
            if (record.physician.is_intern and 
                record.state == 'reviewed' and 
                not record.mentor_comment):
                raise ValidationError('A mentor comment is required for intern diagnoses before they can be reviewed')
