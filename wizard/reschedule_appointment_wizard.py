from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RescheduleAppointmentWizard(models.TransientModel):
    _name = 'hr.hospital.reschedule.appointment.wizard'
    _description = 'Reschedule Appointment Wizard'

    physician_id = fields.Many2one(
        'hr.hospital.physician',
        required=True
    )
    date = fields.Date(
        required=True
    )
    time = fields.Float(
        required=True,
        help='24-hour format (e.g., 13.5 for 1:30 PM)'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_id'):
            visit = self.env[
                'hr.hospital.patient.visits'].browse(self._context.get(
                    'active_id'))
            res.update({
                'physician_id': visit.physician_id.id,
                'date': visit.start_date,
                'time': visit.start_time,
            })
        return res

    @api.constrains('time')
    def _check_time(self):
        for record in self:
            if not 0 <= record.time <= 23.99:
                raise ValidationError(_('Time must be between 0 and 23.99'))
            if record.time < 8 or record.time >= 18:
                raise ValidationError(_(
                    'Appointments can only be scheduled '
                    'between 8:00 and 18:00'))
            # Check if minutes are either .0 or .5 (30 minutes intervals)
            minutes = record.time % 1
            if minutes not in [0.0, 0.5]:
                raise ValidationError(_(
                    'Appointments can only be scheduled at hour or half-hour '
                    'intervals'))

    def _ensure_schedule_slot(self):
        """Ensure schedule slot exists for the selected time."""
        Schedule = self.env['hr.hospital.physician.schedule']
        slot = Schedule.search([
            ('physician_id', '=', self.physician_id.id),
            ('appointment_date', '=', self.date),
            ('appointment_time', '=', self.time)
        ], limit=1)

        # Only create slots on weekdays
        if not slot and self.date.weekday() <= 4:
            slot = Schedule.sudo().create({
                'physician_id': self.physician_id.id,
                'appointment_date': self.date,
                'appointment_time': self.time
            })
        return slot

    @api.onchange('physician_id', 'date', 'time')
    def _check_availability(self):
        if not all([self.physician_id, self.date, self.time]):
            return

        active_id = self._context.get('active_id')
        if not active_id:
            return

        # Check if the new time slot is available
        conflicting_visits = self.env['hr.hospital.patient.visits'].search([
            ('physician_id', '=', self.physician_id.id),
            ('start_date', '=', self.date),
            ('start_time', '=', self.time),
            ('state', 'not in', ['cancelled']),
            ('id', '!=', active_id)
        ])

        if conflicting_visits:
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _(
                        'This time slot is already booked for the selected '
                        'physician!')
                }
            }

    def action_reschedule(self):
        self.ensure_one()
        active_id = self._context.get('active_id')
        if not active_id:
            return

        visit = self.env['hr.hospital.patient.visits'].browse(active_id)

        if visit.state == 'cancelled':
            raise ValidationError(_(
                'Cannot reschedule a cancelled appointment'))

        if visit.state in ['completed', 'in_progress']:
            raise ValidationError(_(
                'Cannot reschedule a completed or in-progress appointment'))

        # Ensure schedule slot exists
        if not self._ensure_schedule_slot():
            raise ValidationError(_(
                'Cannot schedule appointment for this time. '
                'Please select a weekday between 8:00 and 18:00.'))

        # First cancel the old appointment to avoid validation conflicts
        visit.write({
            'state': 'cancelled'
        })

        # Create new appointment with SQL to bypass validations
        new_visit = self.env['hr.hospital.patient.visits'].sudo().with_context(
            skip_schedule_validation=True,  # Add context to skip validations
            mail_create_nosubscribe=True    # Prevent sending notifications
        ).create({
            'physician_id': self.physician_id.id,
            'start_date': self.date,
            'start_time': self.time,
            'state': 'scheduled',
            'patient_id': visit.patient_id.id,
            'notes': visit.notes,
        })

        return {
            'name': _('Rescheduled Appointment'),
            'view_mode': 'form',
            'res_model': 'hr.hospital.patient.visits',
            'res_id': new_visit.id,
            'type': 'ir.actions.act_window',
        }
