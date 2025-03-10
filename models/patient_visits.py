import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PatientVisits(models.Model):
    _name = "hr.hospital.patient.visits"
    _description = "Patient Visits"
    _inherit = ['hr.hospital.time.validation.mixin']
    _sql_constraints = [
        ('unique_physician_datetime',
         'UNIQUE(physician_id, appointment_date, appointment_time)',
         _('This time slot is already booked for this physician!'))
    ]

    appointment_date = fields.Date(
        string='Appointment Date',
        required=True
    )
    appointment_time = fields.Float(
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

    @api.depends('physician_id', 'appointment_date', 'appointment_time')
    def _compute_schedule_slot(self):
        for visit in self:
            if visit.physician_id and visit.appointment_date and visit.appointment_time:
                schedule = self.env['hr.hospital.physician.schedule'].search([
                    ('physician_id', '=', visit.physician_id.id),
                    ('appointment_date', '=', visit.appointment_date),
                    ('appointment_time', '=', visit.appointment_time)
                ], limit=1)
                visit.schedule_id = schedule.id if schedule else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Skip validations if context flag is set
            if self._context.get('skip_schedule_validation'):
                continue

            required_keys = ['physician_id', 'appointment_date', 'appointment_time']
            if all(k in vals for k in required_keys):
                # Lock the schedule slot first to prevent race conditions
                self.env.cr.execute("""
                    SELECT id FROM hr_hospital_physician_schedule
                    WHERE physician_id = %s
                    AND appointment_date = %s
                    AND appointment_time = %s
                    FOR UPDATE NOWAIT
                """, (
                    vals['physician_id'],
                    vals['appointment_date'],
                    vals['appointment_time']
                ))

                existing = self.search([
                    ('physician_id', '=', vals['physician_id']),
                    ('appointment_date', '=', vals['appointment_date']),
                    ('appointment_time', '=', vals['appointment_time']),
                    ('state', 'not in', ['cancelled'])
                ])
                if existing:
                    raise ValidationError(_(
                        'This time slot is already booked for another patient'
                    ))

            # Check if the patient is trying to create a duplicate appointment
            # on the same day
            if 'patient_id' in vals and 'appointment_date' in vals:
                existing_appointment = self.search([
                    ('patient_id', '=', vals['patient_id']),
                    ('appointment_date', '=', vals['appointment_date']),
                    # Ignore cancelled appointments
                    ('state', 'not in', ['cancelled'])
                ], limit=1)

                if existing_appointment:
                    raise ValidationError(_(
                        'This patient already has an '
                        'appointment on the specified date.'
                    ))

        return super(PatientVisits, self).create(vals_list)

    @api.constrains('appointment_time', 'appointment_date')
    def _check_appointment_time(self):
        for record in self:
            # Use mixin for common time validations
            self._validate_time_slot(record.appointment_time)

            # Check if it's a weekend
            if record.appointment_date and record.appointment_date.weekday() > 4:
                raise ValidationError(_(
                    'Appointments cannot be scheduled on weekends'
                ))

            # If the date of the new appointment is in the past
            today = fields.Date.today()
            now = fields.Datetime.now()
            if record.appointment_date < today or (
                    record.appointment_date == today and
                    record.appointment_time < now.hour + now.minute / 60):
                raise ValidationError(_(
                    'You can not make an appointment in the past.'))

    @api.constrains('physician_id', 'appointment_date', 'appointment_time')
    def _check_physician_availability(self):
        """Validate that the appointment matches an available physician schedule slot.
        This check runs for ALL states (including draft) to ensure data integrity.
        
        The validation ensures:
        1. A schedule slot exists for the physician at the given time
        2. No other non-cancelled visits exist for this slot
        """
        for record in self:
            # Always check for schedule availability, regardless of state
            schedule = self.env['hr.hospital.physician.schedule'].search([
                ('physician_id', '=', record.physician_id.id),
                ('appointment_date', '=', record.appointment_date),
                ('appointment_time', '=', record.appointment_time)
            ])
            if not schedule:
                raise ValidationError(_(
                    'Selected time slot is not available in physician\'s '
                    'schedule. Please check the physician\'s schedule first.'
                ))

            # Check for conflicting visits (excluding cancelled ones and self)
            other_visit = self.search([
                ('id', '!=', record.id),
                ('physician_id', '=', record.physician_id.id),
                ('appointment_date', '=', record.appointment_date),
                ('appointment_time', '=', record.appointment_time),
                ('state', 'not in', ['cancelled'])
            ])
            if other_visit:
                raise ValidationError(_(
                    'This time slot is already booked for another patient'
                ))

    def action_schedule(self):
        self.ensure_one()
        # Use a savepoint to ensure atomic operation
        with self.env.cr.savepoint():
            # Lock the schedule slot
            self.env.cr.execute("""
                SELECT id FROM hr_hospital_physician_schedule
                WHERE physician_id = %s
                AND appointment_date = %s
                AND appointment_time = %s
                FOR UPDATE NOWAIT
            """, (self.physician_id.id, self.appointment_date, self.appointment_time))

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
        # Use a savepoint to ensure atomic operation
        with self.env.cr.savepoint():
            if self.state == 'completed':
                raise ValidationError(_('Cannot cancel a completed visit'))
            # Lock the schedule slot
            if self.schedule_id:
                self.env.cr.execute("""
                    SELECT id FROM hr_hospital_physician_schedule
                    WHERE id = %s
                    FOR UPDATE NOWAIT
                """, (self.schedule_id.id,))
            self.state = 'cancelled'

    def write(self, vals):
        # Get the current date and time
        current_datetime = fields.Datetime.now()

        for record in self:
            # Check if the appointment has already taken place
            if record.appointment_date < current_datetime.date() or (
                record.appointment_date == current_datetime.date() and
                record.appointment_time < current_datetime.hour
                    + current_datetime.minute / 60):

                # If the appointment has passed, prohibit changes
                # to the date, time, physician, or patient
                if any(field in vals for field in [
                        'appointment_date', 'appointment_time',
                        'physician_id', 'patient_id']):
                    raise ValidationError(_(
                        'This appointment has already taken '
                        'place and cannot be modified.'
                        ))

        # Call the super method to proceed with the write operation
        return super(PatientVisits, self).write(vals)

    def unlink(self):
        """Prevent deletion of completed visits or visits with diagnosis."""
        for record in self:
            if record.state == 'completed' or record.diagnosis_id:
                raise ValidationError(_(
                    "Cannot delete a completed visit or a visit that has a "
                    "diagnosis. Cancel the visit instead if necessary."))
        return super().unlink()
