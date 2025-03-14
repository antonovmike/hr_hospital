import logging
from datetime import datetime, time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Person(models.AbstractModel):
    _name = 'hr.hospital.person'
    _description = 'Person'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name_last, name_first'

    name_first = fields.Char(
        string='First Name',
        required=True,
        tracking=True,
        index=True
    )
    name_last = fields.Char(
        string='Last Name',
        required=True,
        tracking=True,
        index=True
    )
    display_name = fields.Char(
        string='Full Name',
        compute='_compute_display_name',
        store=True,
        index=True
    )
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    gender = fields.Selection(
        [('male', 'Male'),
         ('female', 'Female'),
         ('other', 'Other')],
        required=True,
        tracking=True,
        index=True
    )
    phone = fields.Char(tracking=True)
    mobile = fields.Char(tracking=True)
    email = fields.Char(tracking=True)
    
    # Standard Odoo image fields
    image_1920 = fields.Image(
        "Image",
        max_width=1920,
        max_height=1920
    )
    image_128 = fields.Image(
        "Image (128)",
        related='image_1920',
        max_width=128,
        max_height=128,
        store=True
    )

    @api.depends('name_first', 'name_last')
    def _compute_display_name(self):
        for record in self:
            record.display_name = ' '.join(
                filter(None, [record.name_first, record.name_last])
            ) or _("Unnamed")

    def _validate_appointment_time(self, appointment_time):
        """Validate appointment time format and range.
        
        Args:
            appointment_time (float): Time in 24-hour format (e.g., 13.5 for 1:30 PM)
        
        Raises:
            ValidationError: If time is invalid
        """
        if not isinstance(appointment_time, (int, float)):
            raise ValidationError(_('Appointment time must be a number'))
        
        hours = int(appointment_time)
        minutes = int((appointment_time % 1) * 60)
        
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValidationError(_(
                'Invalid time format. Use 24-hour format '
                '(e.g., 13.5 for 1:30 PM)'
            ))

    def _validate_appointment_date(self, appointment_date):
        """Validate appointment date.
        
        Args:
            appointment_date (date): The appointment date
        
        Raises:
            ValidationError: If date is invalid
        """
        if not appointment_date:
            raise ValidationError(_('Appointment date is required'))
        
        if appointment_date < fields.Date.today():
            raise ValidationError(_('Cannot schedule appointments in the past'))
        
        if appointment_date.weekday() > 4:  # Saturday or Sunday
            raise ValidationError(_('Cannot schedule appointments on weekends'))

    def _get_appointment_domain(self, physician_id, appointment_date, appointment_time):
        """Get domain for checking appointment conflicts.
        
        This is a helper method to ensure consistent conflict checking
        across different models.
        
        Args:
            physician_id (int): ID of the physician
            appointment_date (date): The appointment date
            appointment_time (float): Time in 24-hour format
        
        Returns:
            list: Domain for searching conflicting appointments
        """
        return [
            ('physician_id', '=', physician_id),
            ('appointment_date', '=', appointment_date),
            ('appointment_time', '=', appointment_time),
            ('state', 'not in', ['cancelled'])
        ]

    def _check_appointment_conflict(self, physician_id, appointment_date, appointment_time):
        """Check for appointment conflicts.
        
        Args:
            physician_id (int): ID of the physician
            appointment_date (date): The appointment date
            appointment_time (float): Time in 24-hour format
        
        Returns:
            bool: True if conflict exists, False otherwise
        """
        domain = self._get_appointment_domain(
            physician_id, appointment_date, appointment_time
        )

        # Check both schedule and visits
        schedule = self.env['hr.hospital.physician.schedule'].search_count(domain)
        visits = self.env['hr.hospital.patient.visits'].search_count(domain)

        return bool(schedule or visits)
