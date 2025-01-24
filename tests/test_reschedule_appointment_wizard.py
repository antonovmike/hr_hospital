from datetime import date, timedelta
from odoo.tests import common
from odoo.exceptions import ValidationError


class TestRescheduleAppointmentWizard(common.TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a physician
        self.physician = self.env['hr.hospital.physician'].create({
            'name_first': 'Dr. John',
            'name_last': 'Smith',
            'is_intern': False,
        })

        # Create patients
        self.patient = self.env['hr.hospital.patient'].create({
            'name_first': 'Jane',
            'name_last': 'Doe',
            'date_of_birth': date(1990, 1, 1),
        })

        self.patient2 = self.env['hr.hospital.patient'].create({
            'name_first': 'John',
            'name_last': 'Smith',
            'date_of_birth': date(1985, 5, 15),
        })

        # Get next weekday for testing
        self.test_date = date.today() + timedelta(days=1)
        while self.test_date.weekday() > 4:  # Skip weekends
            self.test_date += timedelta(days=1)

        # Create schedule slots for 9:00 and 10:00
        self.slot_9am = self.env['hr.hospital.physician.schedule'].create({
            'physician_id': self.physician.id,
            'appointment_date': self.test_date,
            'appointment_time': 9.0,  # 9:00 AM
        })

        self.slot_10am = self.env['hr.hospital.physician.schedule'].create({
            'physician_id': self.physician.id,
            'appointment_date': self.test_date,
            'appointment_time': 10.0,  # 10:00 AM
        })

        # Create an original appointment at 9:00
        self.visit = self.env['hr.hospital.patient.visits'].create({
            'physician_id': self.physician.id,
            'patient_id': self.patient.id,
            'start_date': self.test_date,
            'start_time': 9.0,
            'state': 'scheduled',
        })

    def test_check_availability_no_conflict(self):
        """Test availability check when slot is free"""
        wizard = self.env[
            'hr.hospital.reschedule.appointment.wizard'
        ].with_context(
            active_id=self.visit.id
        ).create({
            'physician_id': self.physician.id,
            'date': self.test_date,
            'time': 10.0,  # Different time than original
        })

        result = wizard._check_availability()
        self.assertFalse(
            result,
            "Should return None when no conflicts exist"
        )

    def test_check_availability_with_conflict(self):
        """Test availability check when slot is already booked"""
        # Create another appointment at 10:00 with a different patient
        self.env['hr.hospital.patient.visits'].create({
            'physician_id': self.physician.id,
            'patient_id': self.patient2.id,  # Use second patient
            'start_date': self.test_date,
            'start_time': 10.0,
            'state': 'scheduled',
        })

        # Try to reschedule to 10:00
        wizard = self.env[
            'hr.hospital.reschedule.appointment.wizard'
        ].with_context(
            active_id=self.visit.id
        ).create({
            'physician_id': self.physician.id,
            'date': self.test_date,
            'time': 10.0,
        })

        result = wizard._check_availability()
        self.assertTrue(
            result and isinstance(result, dict) and 'warning' in result,
            "Should return warning dictionary when conflict exists"
        )
        if result and 'warning' in result:
            self.assertIn(
                'already booked',
                result['warning'].get('message', ''),
                "Warning message should indicate slot is booked"
            )

    def test_reschedule_success(self):
        """Test successful rescheduling of appointment"""
        wizard = self.env[
            'hr.hospital.reschedule.appointment.wizard'
        ].with_context(
            active_id=self.visit.id
        ).create({
            'physician_id': self.physician.id,
            'date': self.test_date,
            'time': 10.0,
        })

        result = wizard.action_reschedule()
        self.assertTrue(
            result and isinstance(result, dict) and 'res_id' in result,
            "Should return action dictionary with res_id"
        )

        # Check that old visit is cancelled
        self.assertEqual(
            self.visit.state,
            'cancelled',
            "Original appointment should be cancelled"
        )

        if result and 'res_id' in result:
            # Find and check new appointment
            new_visit = self.env['hr.hospital.patient.visits'].browse(
                result['res_id'])
            self.assertEqual(
                new_visit.start_time, 10.0, "New time should be 10:00")
            self.assertEqual(
                new_visit.state, 'scheduled', "New visit should be scheduled")
            self.assertEqual(
                new_visit.patient_id,
                self.patient,
                "Patient should be transferred to new appointment"
            )

    def test_reschedule_cancelled_visit(self):
        """Test that cancelled visits cannot be rescheduled"""
        self.visit.state = 'cancelled'

        wizard = self.env[
            'hr.hospital.reschedule.appointment.wizard'
        ].with_context(
            active_id=self.visit.id
        ).create({
            'physician_id': self.physician.id,
            'date': self.test_date,
            'time': 10.0,
        })

        with self.assertRaises(
            ValidationError,
            msg="Should not be able to reschedule cancelled appointment"
        ):
            wizard.action_reschedule()

    def test_reschedule_completed_visit(self):
        """Test that completed visits cannot be rescheduled"""
        self.visit.state = 'completed'

        wizard = self.env[
            'hr.hospital.reschedule.appointment.wizard'
        ].with_context(
            active_id=self.visit.id
        ).create({
            'physician_id': self.physician.id,
            'date': self.test_date,
            'time': 10.0,
        })

        with self.assertRaises(
            ValidationError,
            msg="Should not be able to reschedule completed appointment"
        ):
            wizard.action_reschedule()

    def test_reschedule_to_weekend(self):
        """Test that appointments cannot be rescheduled to weekends"""
        weekend_date = self.test_date
        while weekend_date.weekday() <= 4:  # Find next Saturday
            weekend_date += timedelta(days=1)

        # Create a schedule slot for weekend
        # (this will work since there's no weekend constraint)
        weekend_slot = self.env['hr.hospital.physician.schedule'].create({
            'physician_id': self.physician.id,
            'appointment_date': weekend_date,
            'appointment_time': 10.0,
        })

        # Try to reschedule to weekend
        # (should fail due to appointment validation)
        wizard = self.env[
            'hr.hospital.reschedule.appointment.wizard'
        ].with_context(
            active_id=self.visit.id
        ).create({
            'physician_id': self.physician.id,
            'date': weekend_date,
            'time': 10.0,
        })

        with self.assertRaises(
            ValidationError,
            msg="Should not be able to reschedule to weekend"
        ):
            wizard.action_reschedule()

        # Clean up the weekend slot
        weekend_slot.unlink()
