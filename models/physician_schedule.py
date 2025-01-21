from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PhysicianSchedule(models.Model):
    _name = 'hr.hospital.physician.schedule'
    _description = 'Physician Schedule'
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

    @api.constrains('appointment_time')
    def _check_appointment_time(self):
        for record in self:
            # Check if time is between 8 and 18
            if record.appointment_time < 8 or record.appointment_time >= 18:
                raise ValidationError(_(
                    'Appointment time must be between 8:00 and 17:59'
                ))

            # Check if minutes are either .0 or .5 (30 minutes intervals)
            minutes = record.appointment_time % 1
            if minutes not in [0.0, 0.5]:
                raise ValidationError(_(
                    'Appointments can only be scheduled at hour or half-hour '
                    'intervals'
                ))

    @api.model
    def generate_slots(self, physician_id, start_date, end_date=None):
        """Generate slots for a physician between start_date and end_date."""
        if not end_date:
            end_date = start_date

        # Generate time slots from 8:00 to 17:30 with 30-minute intervals
        time_slots = []
        current_time = 8.0
        while current_time < 18.0:
            time_slots.append(current_time)
            current_time += 0.5

        # Generate slots for each day
        current_date = start_date
        while current_date <= end_date:
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
    def generate_slots_for_physician(self, physician_id):
        """Generate slots for next 5 working days for a physician."""
        today = fields.Date.today()
        # Find next Monday if today is weekend
        if today.weekday() > 4:  # Saturday or Sunday
            start_date = today + timedelta(days=(7 - today.weekday()))
        else:
            start_date = today
        end_date = start_date + timedelta(days=4)  # 5 working days
        self.generate_slots(physician_id, start_date, end_date)
