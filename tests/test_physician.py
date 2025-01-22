from datetime import date, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestPhysician(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a regular physician
        self.physician = self.env['hr.hospital.physician'].create({
            'name_first': 'Test',
            'name_last': 'Physician',
            'specialty': 'General Practice',
            'is_intern': False
        })

        # Create an intern with a mentor
        self.intern = self.env['hr.hospital.physician'].create({
            'name_first': 'Test',
            'name_last': 'Intern',
            'specialty': 'Internal Medicine',
            'is_intern': True,
            'mentor_id': self.physician.id
        })

        # Get future dates for testing
        self.future_date = date.today() + timedelta(days=30)
        self.Schedule = self.env['hr.hospital.physician.schedule']

    def tearDown(self):
        """Clean up test data"""
        self.Schedule.search([
            ('physician_id', 'in', [self.physician.id, self.intern.id])
        ]).unlink()
        super().tearDown()

    def test_create_physician(self):
        """Test creating a regular physician."""
        self.assertTrue(self.physician.id)
        self.assertEqual(self.physician.display_name, 'Test Physician')
        self.assertEqual(self.physician.specialty, 'General Practice')
        self.assertFalse(self.physician.is_intern)
        self.assertFalse(self.physician.mentor_id)

    def test_create_intern(self):
        """Test creating an intern with a mentor."""
        self.assertTrue(self.intern.id)
        self.assertEqual(self.intern.display_name, 'Test Intern')
        self.assertTrue(self.intern.is_intern)
        self.assertEqual(self.intern.mentor_id.id, self.physician.id)

    def test_intern_without_mentor(self):
        """Test that interns must have a mentor."""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.physician'].create({
                'name_first': 'Intern',
                'name_last': 'Without Mentor',
                'specialty': 'Internal Medicine',
                'is_intern': True
            })

    def test_non_intern_with_mentor(self):
        """Test that regular physicians cannot have mentors."""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.physician'].create({
                'name_first': 'Physician',
                'name_last': 'With Mentor',
                'specialty': 'Surgery',
                'is_intern': False,
                'mentor_id': self.physician.id
            })

    def test_intern_as_mentor(self):
        """Test that interns cannot be mentors."""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.physician'].create({
                'name_first': 'Another',
                'name_last': 'Intern',
                'specialty': 'Internal Medicine',
                'is_intern': True,
                'mentor_id': self.intern.id
            })

    def test_self_mentoring(self):
        """Test that physicians cannot mentor themselves."""
        with self.assertRaises(ValidationError):
            self.physician.write({
                'is_intern': True,
                'mentor_id': self.physician.id
            })

    def test_schedule_generation_on_create(self):
        """Test automatic schedule generation when creating a physician."""
        # Create a new physician
        new_physician = self.env['hr.hospital.physician'].create({
            'name_first': 'New',
            'name_last': 'Doctor',
            'specialty': 'Surgery',
            'is_intern': False
        })

        # Check that slots were automatically created
        slots = self.Schedule.search([
            ('physician_id', '=', new_physician.id)
        ])
        self.assertTrue(slots)

        # Verify slots are in the future
        for slot in slots:
            self.assertGreaterEqual(slot.appointment_date, date.today())

    def test_no_schedule_for_intern(self):
        """Test that schedules are not generated for interns."""
        # Try to generate schedule for intern
        with self.assertRaises(ValidationError):
            self.intern.generate_schedule_slots()

        # Verify no slots exist for intern
        intern_slots = self.Schedule.search([
            ('physician_id', '=', self.intern.id)
        ])
        self.assertFalse(intern_slots)

    def test_intern_promotion(self):
        """Test intern promotion to full physician with schedule generation."""
        # Promote intern to full physician
        self.intern.write({
            'is_intern': False,
            'mentor_id': False
        })

        # Generate schedule for newly promoted physician
        self.intern.generate_schedule_slots()

        # Verify slots were created
        slots = self.Schedule.search([
            ('physician_id', '=', self.intern.id)
        ])
        self.assertTrue(slots)

    def test_mentor_intern_relationship(self):
        """Test mentor-intern relationship and constraints."""
        # Check intern appears in mentor's intern_ids
        self.assertIn(self.intern, self.physician.intern_ids)

        # Create another intern for same mentor
        another_intern = self.env['hr.hospital.physician'].create({
            'name_first': 'Another',
            'name_last': 'Intern',
            'specialty': 'Internal Medicine',
            'is_intern': True,
            'mentor_id': self.physician.id
        })

        # Check both interns appear in mentor's intern_ids
        self.assertEqual(len(self.physician.intern_ids), 2)
        self.assertIn(another_intern, self.physician.intern_ids)

    def test_schedule_constraints(self):
        """Test schedule-related constraints."""
        # Try to generate schedule for non-existent physician
        with self.assertRaises(ValidationError):
            self.Schedule.generate_slots(999999, self.future_date)

        # Try to generate schedule for past date
        past_date = date.today() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.Schedule.generate_slots(self.physician.id, past_date)

        # Try to generate schedule with end date before start date
        with self.assertRaises(ValidationError):
            self.Schedule.generate_slots(
                self.physician.id,
                self.future_date,
                self.future_date - timedelta(days=1)
            )

    def test_schedule_generation(self):
        """Test automatic schedule generation for physicians."""
        # Check that slots were created for the regular physician
        slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.physician.id)
        ])
        self.assertTrue(slots)

        # Check that no slots were created for the intern
        intern_slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.intern.id)
        ])
        self.assertFalse(intern_slots)

    def test_manual_schedule_generation(self):
        """Test manual schedule generation."""
        # Clear existing slots
        self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.physician.id)
        ]).unlink()

        # Generate new slots
        self.physician.generate_schedule_slots()

        # Check that slots were created
        slots = self.env['hr.hospital.physician.schedule'].search([
            ('physician_id', '=', self.physician.id)
        ])
        self.assertTrue(slots)

    def test_intern_schedule_generation(self):
        """Test that interns cannot generate schedules."""
        with self.assertRaises(ValidationError):
            self.intern.generate_schedule_slots()
