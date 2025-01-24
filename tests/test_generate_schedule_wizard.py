from datetime import date, timedelta
from odoo.tests import common
from odoo.exceptions import ValidationError


class TestGenerateScheduleWizard(common.TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a regular physician
        self.physician = self.env['hr.hospital.physician'].create({
            'name_first': 'Dr. John',
            'name_last': 'Smith',
            'is_intern': False,
        })

        # Create base wizard
        self.wizard = self.env['hr.hospital.generate.schedule.wizard'].create({
            'physician_id': self.physician.id,
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=4),  # 5 days total
            'clear_existing': True,
            'even_week_morning': True,
            'even_week_afternoon': False,
            'odd_week_morning': False,
            'odd_week_afternoon': True,
        })

    def test_get_week_number(self):
        """Test week number calculation"""
        # Test dates from different weeks
        test_date = date(2025, 1, 1)  # Use a fixed date for testing
        wizard = self.wizard

        # First week of 2025 is odd (week 1)
        self.assertFalse(
            wizard._is_even_week(test_date),
            "First week of 2025 should be odd")

        # Second week of 2025 is even (week 2)
        test_date = date(2025, 1, 8)
        self.assertTrue(
            wizard._is_even_week(test_date),
            "Second week of 2025 should be even")

    def test_schedule_generation_even_week(self):
        """Test schedule generation for even weeks"""
        # Find a date in an even week
        test_date = date.today()
        while not self.wizard._is_even_week(test_date):
            test_date += timedelta(days=1)

        wizard = self.env['hr.hospital.generate.schedule.wizard'].create({
            'physician_id': self.physician.id,
            'date_from': test_date,
            'date_to': test_date,
            'clear_existing': True,
            'even_week_morning': True,
            'even_week_afternoon': False,
            'odd_week_morning': False,
            'odd_week_afternoon': False,
        })

        # Generate schedule
        wizard.action_generate_slots()

        # Check generated slots
        slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.physician.id),
            ('appointment_date', '=', test_date),
        ])

        # Morning shift should have 10 slots (8:00-13:00, every 30 minutes)
        self.assertEqual(len(slots), 10)
        # Verify all slots are morning slots
        for slot in slots:
            self.assertTrue(
                8.0 <= slot.appointment_time < 13.0,
                "All slots should be morning slots")

    def test_schedule_generation_odd_week(self):
        """Test schedule generation for odd weeks"""
        # Find a date in an odd week
        test_date = date.today()
        while self.wizard._is_even_week(test_date):
            test_date += timedelta(days=1)

        wizard = self.env['hr.hospital.generate.schedule.wizard'].create({
            'physician_id': self.physician.id,
            'date_from': test_date,
            'date_to': test_date,
            'clear_existing': True,
            'even_week_morning': False,
            'even_week_afternoon': False,
            'odd_week_morning': False,
            'odd_week_afternoon': True,
        })

        # Generate schedule
        wizard.action_generate_slots()

        # Check generated slots
        slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.physician.id),
            ('appointment_date', '=', test_date),
        ])

        # Afternoon shift should have 10 slots (13:00-18:00, every 30 minutes)
        self.assertEqual(len(slots), 10)
        # Verify all slots are afternoon slots
        for slot in slots:
            self.assertTrue(
                13.0 <= slot.appointment_time < 18.0,
                "All slots should be afternoon slots")

    def test_clear_existing_slots(self):
        """Test clearing existing slots before generation"""
        # Use a future date to avoid conflicts, ensure it's a weekday
        test_date = date.today() + timedelta(days=30)
        # Adjust to next Monday if it falls on weekend
        while test_date.weekday() > 4:  # 5 = Saturday, 6 = Sunday
            test_date += timedelta(days=1)

        # First, ensure no slots exist for this date
        self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.physician.id),
            ('appointment_date', '=', test_date),
        ]).unlink()

        # Create an existing slot
        self.env['hr.hospital.physician.schedule'].create({
            'physician_id': self.physician.id,
            'appointment_date': test_date,
            'appointment_time': 8.0,
        })

        # Create wizard for the specific date
        wizard = self.env['hr.hospital.generate.schedule.wizard'].create({
            'physician_id': self.physician.id,
            'date_from': test_date,
            'date_to': test_date,
            'clear_existing': True,
            'even_week_morning': True,
            'even_week_afternoon': True,
            'odd_week_morning': True,
            # Enable all shifts to ensure slots are created
            'odd_week_afternoon': True,
        })

        # Generate new schedule
        wizard.action_generate_slots()

        # Count slots
        slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.physician.id),
            ('appointment_date', '=', test_date),
        ])

        # Should have exactly 20 slots (10 morning + 10 afternoon)
        self.assertEqual(
            len(slots), 20,
            f"Expected 20 slots but got {len(slots)} for date {test_date} "
            f"(weekday: {test_date.weekday()})"
        )

    def test_intern_creation_and_validation(self):
        """Test intern creation and schedule generation validation"""
        # First create a mentor
        mentor = self.env['hr.hospital.physician'].create({
            'name_first': 'Dr. Mentor',
            'name_last': 'Senior',
            'is_intern': False,
        })

        # Create an intern with mentor
        intern = self.env['hr.hospital.physician'].create({
            'name_first': 'Dr. Intern',
            'name_last': 'Junior',
            'is_intern': True,
            'mentor_id': mentor.id,
        })

        # Verify intern was created correctly
        self.assertTrue(intern.is_intern, "Should be marked as intern")
        self.assertEqual(
            intern.mentor_id.id,
            mentor.id,
            "Mentor should be correctly assigned"
        )

        # Try to generate schedule for intern
        test_date = date.today() + timedelta(days=30)
        # Ensure it's a weekday
        while test_date.weekday() > 4:  # 5 = Saturday, 6 = Sunday
            test_date += timedelta(days=1)

        wizard = self.env['hr.hospital.generate.schedule.wizard'].create({
            'physician_id': intern.id,
            'date_from': test_date,
            'date_to': test_date,
            'clear_existing': True,
            'even_week_morning': True,
            'even_week_afternoon': True,
        })

        # Verify that schedule generation fails for intern
        with self.assertRaises(
            ValidationError,
            msg="Should not be able to generate schedule for interns"
        ):
            wizard.action_generate_slots()

        # Create schedule for mentor (should work)
        mentor_wizard = self.env[
            'hr.hospital.generate.schedule.wizard'
        ].create({
            'physician_id': mentor.id,
            'date_from': test_date,
            'date_to': test_date,
            'clear_existing': True,
            'even_week_morning': True,
            'even_week_afternoon': True,
        })
        mentor_wizard.action_generate_slots()

        # Verify mentor schedule was created
        mentor_slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', mentor.id),
            ('appointment_date', '=', test_date),
        ])
        self.assertTrue(
            len(mentor_slots) > 0,
            "Schedule should be generated for mentor"
        )

        # Verify no schedule was created for intern
        intern_slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', intern.id),
            ('appointment_date', '=', test_date),
        ])
        self.assertEqual(
            len(intern_slots),
            0,
            "No schedule should exist for intern"
        )

    def test_date_validation(self):
        """Test date validation constraints"""
        # Test end date before start date
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.generate.schedule.wizard'].create({
                'physician_id': self.physician.id,
                'date_from': date.today(),
                'date_to': date.today() - timedelta(days=1),
            })

        # Test past date
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.generate.schedule.wizard'].create({
                'physician_id': self.physician.id,
                'date_from': date.today() - timedelta(days=1),
                'date_to': date.today(),
            })

    def test_time_slot_generation(self):
        """Test the time slot generation logic"""
        wizard = self.env['hr.hospital.generate.schedule.wizard'].create({
            'physician_id': self.physician.id,
            'date_from': date.today(),
            'date_to': date.today(),
        })

        # Test morning slots
        morning_slots = wizard._get_time_slots(True)
        self.assertEqual(len(morning_slots), 10)
        self.assertEqual(morning_slots[0], 8.0)  # First slot at 8:00
        self.assertEqual(morning_slots[-1], 12.5)  # Last slot at 12:30

        # Test afternoon slots
        afternoon_slots = wizard._get_time_slots(False)
        self.assertEqual(len(afternoon_slots), 10)
        self.assertEqual(afternoon_slots[0], 13.0)  # First slot at 13:00
        self.assertEqual(afternoon_slots[-1], 17.5)  # Last slot at 17:30

        # Verify 30-minute intervals
        for i in range(1, len(morning_slots)):
            self.assertEqual(
                morning_slots[i] - morning_slots[i-1],
                0.5,
                "Morning slots should be 30 minutes apart"
            )

        for i in range(1, len(afternoon_slots)):
            self.assertEqual(
                afternoon_slots[i] - afternoon_slots[i-1],
                0.5,
                "Afternoon slots should be 30 minutes apart"
            )
