from odoo import models, _
from odoo.exceptions import ValidationError


class TimeValidationMixin(models.AbstractModel):
    _name = 'hr.hospital.time.validation.mixin'
    _description = 'Time Validation Mixin'

    def _validate_time_slot(self, time_value):
        """Common time slot validation logic.
        Args:
            time_value (float): Time in 24-hour format (e.g., 13.5 for 1:30 PM)
        Raises:
            ValidationError: If time validation fails
        """
        # Check if time is between 8 and 18
        if time_value < 8 or time_value >= 18:
            raise ValidationError(_(
                'Appointment time must be between 8:00 and 17:59'
            ))

        # Check if minutes are either .0 or .5 (30 minutes intervals)
        minutes = time_value % 1
        if minutes not in [0.0, 0.5]:
            raise ValidationError(_(
                'Appointments can only be scheduled at hour or half-hour '
                'intervals'
            ))
