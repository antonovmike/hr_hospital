from datetime import timedelta
from psycopg2.errors import UniqueViolation

from odoo.tests import TransactionCase
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger


class TestPhysicianSchedule(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a test physician
        self.physician = self.env['hr.hospital.physician'].create({
            'name_first': 'John',
            'name_last': 'Smith',
            'specialty': 'General',
            'is_intern': False
        })

    def test_appointment_time_validation(self):
        """Test appointment time validation constraints"""
        # Valid time should work (9:30)
        schedule = self.env['hr.hospital.physician.schedule'].create({
            'physician_id': self.physician.id,
            'appointment_date': fields.Date.today() + timedelta(days=1),
            'appointment_time': 9.5
        })
        self.assertTrue(schedule.exists())

        # Test invalid times
        invalid_times = [
            (7.5, 'before 8:00'),
            (18.0, 'at or after 18:00'),
            (9.25, 'not at half-hour interval'),
            (10.75, 'not at half-hour interval')
        ]

        for time, description in invalid_times:
            appointment_date = fields.Date.today() + timedelta(days=1)
            with self.assertRaises(
                ValidationError,
                msg=f'Should not allow time {description}'
            ):
                self.env['hr.hospital.physician.schedule'].create({
                    'physician_id': self.physician.id,
                    'appointment_date': appointment_date,
                    'appointment_time': time
                })

    def test_unique_physician_datetime_constraint(self):
        """Test unique constraint for physician datetime combination"""
        tomorrow = fields.Date.today() + timedelta(days=1)
        # Make sure tomorrow is a weekday
        while tomorrow.weekday() > 4:  # If it's weekend
            tomorrow += timedelta(days=1)

        # Create first appointment
        appointment_time = 9.0
        schedule1 = self.env['hr.hospital.physician.schedule'].create({
            'physician_id': self.physician.id,
            'appointment_date': tomorrow,
            'appointment_time': appointment_time
        })
        self.assertTrue(schedule1.exists())

        # Try to create another appointment for the same datetime
        # Use mute_logger to suppress the error log from the database
        with self.assertRaises(
            UniqueViolation,
            msg='Should not allow duplicate appointments'
        ), mute_logger('odoo.sql_db'):
            self.env['hr.hospital.physician.schedule'].create({
                'physician_id': self.physician.id,
                'appointment_date': tomorrow,
                'appointment_time': appointment_time
            })

    def test_generate_slots(self):
        """Test slot generation functionality"""
        tomorrow = fields.Date.today() + timedelta(days=1)
        # Make sure tomorrow is a weekday
        while tomorrow.weekday() > 4:  # If it's weekend
            tomorrow += timedelta(days=1)

        # Generate slots for tomorrow
        schedule = self.env['hr.hospital.physician.schedule']
        schedule.generate_slots(self.physician.id, tomorrow)

        # Count generated slots
        slots = schedule.search([
            ('physician_id', '=', self.physician.id),
            ('appointment_date', '=', tomorrow)
        ])

        # Should have 20 slots (8:00-17:30, every 30 minutes)
        self.assertEqual(
            len(slots), 20,
            'Incorrect number of slots generated'
        )

        # Verify slot times
        for slot in slots:
            # Time should be between 8:00 and 17:30
            self.assertGreaterEqual(slot.appointment_time, 8.0)
            self.assertLess(slot.appointment_time, 18.0)
            # Time should be at hour or half-hour
            self.assertIn(slot.appointment_time % 1, [0.0, 0.5])

    def test_generate_slots_validation(self):
        """Test validation rules for slot generation"""
        # Create a mentor for the intern
        mentor = self.env['hr.hospital.physician'].create({
            'name_first': 'Senior',
            'name_last': 'Doctor',
            'specialty': 'General',
            'is_intern': False
        })

        # Test generating slots for intern
        intern = self.env['hr.hospital.physician'].create({
            'name_first': 'Intern',
            'name_last': 'Doctor',
            'specialty': 'General',
            'is_intern': True,
            'mentor_id': mentor.id  # Assign the mentor
        })

        with self.assertRaises(
            ValidationError,
            msg='Should not generate slots for interns'
        ):
            self.env[
                'hr.hospital.physician.schedule'
            ].generate_slots_for_physician(
                intern.id
            )

    def test_generate_next_week_slots(self):
        """Test generation of next week's slots"""
        schedule = self.env['hr.hospital.physician.schedule'].create({
            'physician_id': self.physician.id,
            'appointment_date': fields.Date.today() + timedelta(days=1),
            'appointment_time': 9.0
        })

        schedule.generate_next_week_slots()

        # Calculate next week's date range
        today = fields.Date.today()
        next_week_start = today + timedelta(days=(7 - today.weekday()))
        next_week_end = next_week_start + timedelta(days=4)

        # Check if slots were generated for next week
        next_week_slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.physician.id),
            ('appointment_date', '>=', next_week_start),
            ('appointment_date', '<=', next_week_end)
        ])

        # Should have 20 slots per day for 5 weekdays
        self.assertEqual(
            len(next_week_slots), 100,
            'Should generate 100 slots for next week (20 slots * 5 days)'
        )
