import logging
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Patient(models.Model):
    _name = 'hr.hospital.patient'
    _inherit = ['hr.hospital.person']
    _description = 'Patient'

    # Personal Information
    date_of_birth = fields.Date(tracking=True)
    age = fields.Integer(compute='_compute_age', store=True)
    passport_details = fields.Char(tracking=True)
    contact_person = fields.Char(
        string='Emergency Contact',
        tracking=True,
        help='Name of person to contact in case of emergency'
    )

    # Medical Information
    personal_physician = fields.Many2one(
        comodel_name='hr.hospital.physician',
        string='Primary Physician',
        tracking=True,
        domain="[('is_intern', '=', False)]"
    )
    disease_ids = fields.Many2many(
        comodel_name='hr.hospital.disease',
        string='Conditions',
        tracking=True
    )
    
    # Visits and Appointments
    visit_ids = fields.One2many(
        comodel_name='hr.hospital.patient.visits',
        inverse_name='patient_id',
        string='Visits'
    )
    next_appointment_date = fields.Date(
        compute='_compute_next_appointment',
        store=True,
        string='Next Appointment Date'
    )
    next_appointment_time = fields.Float(
        compute='_compute_next_appointment',
        store=True,
        string='Next Appointment Time'
    )

    @api.depends('date_of_birth')
    def _compute_age(self):
        """Compute patient age based on date of birth."""
        for rec in self:
            if rec.date_of_birth:
                rec.age = relativedelta(
                    date.today(),
                    date(
                        rec.date_of_birth.year,
                        rec.date_of_birth.month,
                        rec.date_of_birth.day
                    ),
                ).years
            else:
                rec.age = False

    @api.depends('visit_ids', 'visit_ids.appointment_date', 'visit_ids.appointment_time', 'visit_ids.state')
    def _compute_next_appointment(self):
        """Compute the next scheduled appointment."""
        for patient in self:
            next_visit = patient.visit_ids.filtered(
                lambda v: v.state == 'scheduled' and v.appointment_date >= fields.Date.today()
            ).sorted(lambda v: (v.appointment_date, v.appointment_time))[:1]
            
            patient.next_appointment_date = next_visit.appointment_date if next_visit else False
            patient.next_appointment_time = next_visit.appointment_time if next_visit else False

    def action_view_visits(self):
        """Open the visits view for this patient."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Patient Visits'),
            'res_model': 'hr.hospital.patient.visits',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def write(self, vals):
        """Override write to track physician changes."""
        if 'personal_physician' in vals:
            self.env['hr.hospital.physician.change.history'].create({
                'date_established': fields.Datetime.now(),
                'patient_id': self.id,
                'physician_id': vals['personal_physician'],
            })
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to track initial physician assignment."""
        records = super().create(vals_list)
        for record in records:
            if record.personal_physician:
                self.env['hr.hospital.physician.change.history'].create({
                    'date_established': fields.Datetime.now(),
                    'patient_id': record.id,
                    'physician_id': record.personal_physician.id,
                })
        return records
