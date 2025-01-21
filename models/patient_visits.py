import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PatientVisits(models.Model):
    _name = "hr.hospital.patient.visits"
    _description = "Patient Visits"
    _sql_constraints = [
        ('unique_appointment',
         'UNIQUE(physician_id, start_date, start_time)',
         _('This time slot is already booked for this physician!'))
    ]

    start_date = fields.Date(
        string='Appointment Date',
        required=True
    )
    start_time = fields.Float(
        string='Appointment Time',
        required=True,
        help='24-hour format (e.g., 13.5 for 1:30 PM)'
    )
    state = fields.Selection([
        ('draft', _('Draft')),
        ('scheduled', _('Scheduled')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled'))
    ], default='draft', required=True, string='Status')
    physician_id = fields.Many2one(
        comodel_name='hr.hospital.physician',
        string='Physician',
        required=True
    )
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True
    )
    diagnosis_id = fields.Many2one(
        comodel_name='hr.hospital.diagnosis',
        string='Diagnosis',
    )
    notes = fields.Text(string='Visit Notes')
    schedule_id = fields.Many2one(
        'hr.hospital.physician.schedule',
        string='Schedule Slot',
        compute='_compute_schedule_slot',
        store=True
    )

    @api.depends('physician_id', 'start_date', 'start_time')
    def _compute_schedule_slot(self):
        for visit in self:
            if visit.physician_id and visit.start_date and visit.start_time:
                schedule = self.env['hr.hospital.physician.schedule'].search([
                    ('physician_id', '=', visit.physician_id.id),
                    ('appointment_date', '=', visit.start_date),
                    ('appointment_time', '=', visit.start_time)
                ], limit=1)
                visit.schedule_id = schedule.id if schedule else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            required_keys = ['physician_id', 'start_date', 'start_time']
            if all(k in vals for k in required_keys):
                existing = self.search([
                    ('physician_id', '=', vals['physician_id']),
                    ('start_date', '=', vals['start_date']),
                    ('start_time', '=', vals['start_time']),
                    ('state', 'not in', ['cancelled'])
                ])
                if existing:
                    raise ValidationError(_(
                        'This time slot is already booked for another patient'
                    ))

        return super().create(vals_list)

    @api.constrains('start_time')
    def _check_appointment_time(self):
        for record in self:
            if record.start_time < 8 or record.start_time >= 18:
                raise ValidationError(_(
                    'Appointment time must be between 8:00 and 17:59'
                ))

            minutes = record.start_time % 1
            if minutes not in [0.0, 0.5]:
                raise ValidationError(_(
                    'Appointments can only be scheduled at hour or half-hour '
                    'intervals'
                ))

            # Check if it's a weekend
            if record.start_date and record.start_date.weekday() > 4:
                raise ValidationError(_(
                    'Appointments cannot be scheduled on weekends'
                ))

    @api.constrains('physician_id', 'start_date', 'start_time', 'state')
    def _check_physician_availability(self):
        for record in self:
            if record.state not in ['draft', 'cancelled']:
                schedule = self.env['hr.hospital.physician.schedule'].search([
                    ('physician_id', '=', record.physician_id.id),
                    ('appointment_date', '=', record.start_date),
                    ('appointment_time', '=', record.start_time)
                ])
                if not schedule:
                    raise ValidationError(_(
                        'Selected time slot is not available in physician\'s '
                        'schedule'
                    ))

                other_visit = self.search([
                    ('id', '!=', record.id),
                    ('physician_id', '=', record.physician_id.id),
                    ('start_date', '=', record.start_date),
                    ('start_time', '=', record.start_time),
                    ('state', 'not in', ['cancelled'])
                ])
                if other_visit:
                    raise ValidationError(_(
                        'This time slot is already booked for another patient'
                    ))

    def action_schedule(self):
        self.ensure_one()
        if not self.schedule_id:
            raise ValidationError(_(
                'No available slot found in physician\'s schedule'
            ))
        self._check_physician_availability()
        self.state = 'scheduled'
        return True

    def action_start(self):
        self.ensure_one()
        self.state = 'in_progress'

    def action_complete(self):
        self.ensure_one()
        if not self.diagnosis_id:
            raise ValidationError(_(
                'Please add a diagnosis before completing the visit'
            ))
        self.state = 'completed'

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'completed':
            raise ValidationError(_('Cannot cancel a completed visit'))
        self.state = 'cancelled'

    def write(self, vals):
        """Override write to prevent modification of completed visits."""
        for record in self:
            if record.state == 'completed':
                restricted_fields = {
                    'start_date', 'start_time', 'physician_id', 'patient_id'
                }
                if any(field in vals for field in restricted_fields):
                    raise ValidationError(_(
                        'Cannot modify the date/time, physician, or patient '
                        'of a completed visit.'
                    ))
        return super().write(vals)

    def unlink(self):
        """Prevent deletion of completed visits or visits with diagnosis."""
        for record in self:
            if record.state == 'completed' or record.diagnosis_id:
                raise ValidationError(_(
                    "Cannot delete a completed visit or a visit that has a "
                    "diagnosis. Cancel the visit instead if necessary."
                ))
        return super().unlink()
