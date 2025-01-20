from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestPhysician(TransactionCase):

    def setUp(self):
        super().setUp()
        self.physician = self.env['hr.hospital.physician'].create({
            'name': 'Test Physician',
            'specialty': 'General Practice',
            'is_intern': False
        })

        self.intern = self.env['hr.hospital.physician'].create({
            'name': 'Test Intern',
            'specialty': 'Internal Medicine',
            'is_intern': True,
            'mentor_id': self.physician.id
        })

    def test_create_physician(self):
        """Test creating a regular physician."""
        self.assertTrue(self.physician.id)
        self.assertEqual(self.physician.name, 'Test Physician')
        self.assertEqual(self.physician.specialty, 'General Practice')
        self.assertFalse(self.physician.is_intern)
        self.assertFalse(self.physician.mentor_id)

    def test_create_intern(self):
        """Test creating an intern with a mentor."""
        self.assertTrue(self.intern.id)
        self.assertEqual(self.intern.name, 'Test Intern')
        self.assertTrue(self.intern.is_intern)
        self.assertEqual(self.intern.mentor_id.id, self.physician.id)

    def test_intern_without_mentor(self):
        """Test that interns must have a mentor."""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.physician'].create({
                'name': 'Intern Without Mentor',
                'specialty': 'Internal Medicine',
                'is_intern': True
            })

    def test_non_intern_with_mentor(self):
        """Test that regular physicians cannot have mentors."""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.physician'].create({
                'name': 'Physician With Mentor',
                'specialty': 'Surgery',
                'is_intern': False,
                'mentor_id': self.physician.id
            })

    def test_intern_as_mentor(self):
        """Test that interns cannot be mentors."""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.physician'].create({
                'name': 'Another Intern',
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
