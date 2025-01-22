from odoo import models, fields
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class MassReassignPhysicianWizard(models.TransientModel):
    _name = 'hr.hospital.mass.reassign.physician.wizard'
    _description = 'Mass Reassign Physician Wizard'

    physician_id = fields.Many2one(
        'hr.hospital.physician',
        string='New Physician',
        required=True,
        domain=[('is_intern', '=', False)]
    )
    patient_ids = fields.Many2many(
        'hr.hospital.patient',
        'mass_reassign_physician_rel',
        'wizard_id',
        'patient_id',
        string='Patients',
        readonly=True
    )

    def action_reassign_physician(self):
        self.ensure_one()
        if not self.patient_ids:
            raise ValidationError(_("No patients selected for reassignment."))

        for patient in self.patient_ids:
            # Create history record for the change
            self.env['hr.hospital.physician.change.history'].create({
                'patient_id': patient.id,
                'physician_id': self.physician_id.id,
                'date_established': fields.Datetime.now(),
            })

            # Update patient's physician
            patient.write({
                'personal_physician': self.physician_id.id
            })

        return {'type': 'ir.actions.act_window_close'}
