from datetime import timedelta, date
from calendar import monthrange
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PhysicianSchedule(models.Model):
    _name = 'hr.hospital.physician.schedule'
    _description = 'Physician Schedule'
    _inherit = ['hr.hospital.time.validation.mixin']
    _sql_constraints = [
        ('unique_physician_datetime',
         'UNIQUE(physician_id, appointment_date, appointment_time)',
         'This time slot is already scheduled for this physician!')
    ]

    physician_id = fields.Many2one(
        'hr.hospital.physician',
        string='Physician',
        required=True
    )
    appointment_date = fields.Date(
        string='Date of Appointment',
        required=True
    )
    appointment_time = fields.Float(
        string='Time of Appointment',
        required=True,
        help='24-hour format (e.g., 13.5 for 1:30 PM)'
    )
    visit_ids = fields.One2many(
        'hr.hospital.patient.visits',
        'schedule_id',
        string='Visits',
        help='Visits scheduled for this time slot'
    )
    is_available = fields.Boolean(
        string='Is Available',
        compute='_compute_is_available',
        help='Indicates if this time slot is available for scheduling'
    )

    @api.depends('visit_ids.state')
    def _compute_is_available(self):
        for record in self:
            # A slot is available if it has no visits
            # or all visits are cancelled
            record.is_available = not bool(record.visit_ids.filtered(
                lambda v: v.state != 'cancelled'
            ))

    @api.constrains('appointment_time')
    def _check_appointment_time(self):
        for record in self:
            self._validate_time_slot(record.appointment_time)

    @api.model
    def generate_slots(self, physician_id, start_date, end_date=None):
        """Generate slots for a physician between start_date and end_date."""
        # Check if physician exists and is not an intern
        physician = self.env['hr.hospital.physician'].browse(physician_id)
        if not physician.exists():
            raise ValidationError(_('Physician not found'))
        if physician.is_intern:
            raise ValidationError(_('Cannot generate schedule for interns'))

        if not end_date:
            end_date = start_date

        # Check dates
        today = fields.Date.today()
        if start_date < today:
            raise ValidationError(_('Cannot generate slots for past dates'))
        if end_date < start_date:
            raise ValidationError(_('End date cannot be before start date'))

        # Generate time slots from 8:00 to 17:30 with 30-minute intervals
        time_slots = []
        current_time = 8.0
        while current_time < 18.0:
            time_slots.append(current_time)
            current_time += 0.5

        # Generate slots for each day
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() <= 4:  # Monday to Friday
                for time_slot in time_slots:
                    # Check if slot already exists
                    existing = self.search([
                        ('physician_id', '=', physician_id),
                        ('appointment_date', '=', current_date),
                        ('appointment_time', '=', time_slot)
                    ])
                    if not existing:
                        self.create({
                            'physician_id': physician_id,
                            'appointment_date': current_date,
                            'appointment_time': time_slot
                        })
            current_date += timedelta(days=1)
        return True

    def generate_next_week_slots(self):
        """Generate slots for next week for this physician."""
        self.ensure_one()
        today = fields.Date.today()
        next_week_start = today + timedelta(days=(7 - today.weekday()))
        next_week_end = next_week_start + timedelta(days=4)  # Monday to Friday
        self.generate_slots(
            self.physician_id.id,
            next_week_start,
            next_week_end
        )

    @api.model
    def generate_slots_for_physician(self, physician_id, target_date=None):
        """Generate slots for a specific date for a physician."""
        # Check if physician exists and is not an intern
        physician = self.env['hr.hospital.physician'].browse(physician_id)
        if not physician.exists():
            raise ValidationError(_('Physician not found'))
        if physician.is_intern:
            raise ValidationError(_('Cannot generate schedule for interns'))

        if not target_date:
            target_date = fields.Date.today()

        # Don't generate slots for weekends
        if target_date.weekday() > 4:  # Saturday or Sunday
            return False

        # Generate slots for the specified date
        self.generate_slots(physician_id, target_date, target_date)
        return True

    @api.model
    def generate_month_slots(self, physician_id, year, month):
        """Generate slots for an entire month for a physician."""
        try:
            # Validate month and year
            if not 1 <= month <= 12:
                raise ValidationError(_('Month must be between 1 and 12'))
            if year < fields.Date.today().year:
                raise ValidationError(_(
                    'Cannot generate slots for past years'))

            # Get the first and last day of the month
            last_day = monthrange(year, month)[1]
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)

            # Generate slots
            return self.generate_slots(physician_id, start_date, end_date)
        except ValueError as e:
            raise ValidationError(
                _('Invalid month/year combination: %s') % str(e))
