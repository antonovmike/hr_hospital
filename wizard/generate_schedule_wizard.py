from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class GenerateScheduleWizard(models.TransientModel):
    _name = 'hr.hospital.generate.schedule.wizard'
    _description = 'Generate Schedule Wizard'

    physician_id = fields.Many2one(
        'hr.hospital.physician',
        string='Physician',
        required=True
    )
    date_from = fields.Date(
        string='From Date',
        required=True,
        default=fields.Date.context_today
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=fields.Date.context_today
    )
    clear_existing = fields.Boolean(
        string='Clear Existing Slots',
        help='If checked, existing slots in the date range will be removed '
        'before generating new ones'
    )
    # Even week schedule
    even_week_morning = fields.Boolean(
        string='Even Week Morning (8:00-13:00)',
        default=True,
        help='Schedule for morning shifts (8:00-13:00) on even weeks'
    )
    even_week_afternoon = fields.Boolean(
        string='Even Week Afternoon (13:00-18:00)',
        help='Schedule for afternoon shifts (13:00-18:00) on even weeks'
    )
    # Odd week schedule
    odd_week_morning = fields.Boolean(
        string='Odd Week Morning (8:00-13:00)',
        help='Schedule for morning shifts (8:00-13:00) on odd weeks'
    )
    odd_week_afternoon = fields.Boolean(
        string='Odd Week Afternoon (13:00-18:00)',
        default=True,
        help='Schedule for afternoon shifts (13:00-18:00) on odd weeks'
    )

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            # Set end date to the end of the week by default
            days_ahead = 4 - self.date_from.weekday()  # 4 = Friday
            if days_ahead < 0:
                days_ahead += 7  # If we're past Friday, go to next Friday
            self.date_to = self.date_from + timedelta(days=days_ahead)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError(_(
                    'End date cannot be before start date'))
            if record.date_from < fields.Date.today():
                raise ValidationError(_(
                    'Cannot generate slots for past dates'))

    def _get_time_slots(self, is_morning):
        """Generate time slots for morning or afternoon shift."""
        slots = []
        if is_morning:
            current_time = 8.0
            end_time = 13.0
        else:
            current_time = 13.0
            end_time = 18.0

        while current_time < end_time:
            slots.append(current_time)
            current_time += 0.5
        return slots

    def _is_even_week(self, date):
        """Check if the given date falls in an even week number."""
        return date.isocalendar()[1] % 2 == 0

    def action_generate_slots(self):
        self.ensure_one()

        Schedule = self.env['hr.hospital.physician.schedule']

        # Check if physician is an intern
        if self.physician_id.is_intern:
            raise ValidationError(_('Cannot generate schedule for interns'))

        # Clear existing slots if requested
        if self.clear_existing:
            existing_slots = Schedule.search([
                ('physician_id', '=', self.physician_id.id),
                ('appointment_date', '>=', self.date_from),
                ('appointment_date', '<=', self.date_to),
            ])
            existing_slots.unlink()

        # Generate slots for each day
        current_date = self.date_from
        slots_created = 0

        while current_date <= self.date_to:
            # Skip weekends
            if current_date.weekday() <= 4:  # Monday to Friday
                is_even = self._is_even_week(current_date)

                # Morning shift
                if (is_even and self.even_week_morning) or \
                   (not is_even and self.odd_week_morning):
                    morning_slots = self._get_time_slots(True)
                    for time_slot in morning_slots:
                        if not Schedule.search([
                            ('physician_id', '=', self.physician_id.id),
                            ('appointment_date', '=', current_date),
                            ('appointment_time', '=', time_slot)
                        ], limit=1):
                            Schedule.create({
                                'physician_id': self.physician_id.id,
                                'appointment_date': current_date,
                                'appointment_time': time_slot
                            })
                            slots_created += 1

                # Afternoon shift
                if (is_even and self.even_week_afternoon) or \
                   (not is_even and self.odd_week_afternoon):
                    afternoon_slots = self._get_time_slots(False)
                    for time_slot in afternoon_slots:
                        if not Schedule.search([
                            ('physician_id', '=', self.physician_id.id),
                            ('appointment_date', '=', current_date),
                            ('appointment_time', '=', time_slot)
                        ], limit=1):
                            Schedule.create({
                                'physician_id': self.physician_id.id,
                                'appointment_date': current_date,
                                'appointment_time': time_slot
                            })
                            slots_created += 1

            current_date += timedelta(days=1)

        # Show success message
        message = _(
            '%(count)d schedule slots have been generated for %(name)s') % {
            'count': slots_created,
            'name': self.physician_id.display_name
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'sticky': False,
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
            }
        }
