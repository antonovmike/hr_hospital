from odoo import models, fields, api
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
                raise ValidationError('Appointment time must be between 8:00 and 17:59')
            
            # Check if minutes are either .0 or .5 (30 minutes intervals)
            minutes = record.appointment_time % 1
            if minutes not in [0.0, 0.5]:
                raise ValidationError('Appointments can only be scheduled at hour or half-hour intervals')
