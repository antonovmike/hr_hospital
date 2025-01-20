from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestPhysician(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create mentor physician
        self.mentor = self.env['hr.hospital.physician'].create({
            'name_first': 'Senior',
            'name_last': 'Doctor',
            'specialty': 'Surgery',
            'is_intern': False
        })

    def test_create_intern(self):
        """Test creating an intern with a mentor"""
        intern = self.env['hr.hospital.physician'].create({
            'name_first': 'Junior',
            'name_last': 'Doctor',
            'specialty': 'Surgery',
            'is_intern': True,
            'mentor_id': self.mentor.id
        })
        
        self.assertTrue(intern.id)
        self.assertTrue(intern.is_intern)
        self.assertEqual(intern.mentor_id.id, self.mentor.id)
        self.assertEqual(intern.display_name, 'Junior Doctor')

    def test_intern_without_mentor(self):
        """Test that interns must have a mentor"""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.physician'].create({
                'name_first': 'Junior',
                'name_last': 'Doctor',
                'specialty': 'Surgery',
                'is_intern': True
            })

    def test_intern_cannot_be_mentor(self):
        """Test that interns cannot be mentors"""
        intern1 = self.env['hr.hospital.physician'].create({
            'name_first': 'First',
            'name_last': 'Intern',
            'specialty': 'Surgery',
            'is_intern': True,
            'mentor_id': self.mentor.id
        })
        
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.physician'].create({
                'name_first': 'Second',
                'name_last': 'Intern',
                'specialty': 'Surgery',
                'is_intern': True,
                'mentor_id': intern1.id
            })

    def test_mentor_intern_relationship(self):
        """Test the relationship between mentor and interns"""
        intern1 = self.env['hr.hospital.physician'].create({
            'name_first': 'First',
            'name_last': 'Intern',
            'specialty': 'Surgery',
            'is_intern': True,
            'mentor_id': self.mentor.id
        })
        
        intern2 = self.env['hr.hospital.physician'].create({
            'name_first': 'Second',
            'name_last': 'Intern',
            'specialty': 'Surgery',
            'is_intern': True,
            'mentor_id': self.mentor.id
        })
        
        # Check that both interns are in the mentor's intern_ids
        self.assertEqual(len(self.mentor.intern_ids), 2)
        self.assertIn(intern1.id, self.mentor.intern_ids.ids)
        self.assertIn(intern2.id, self.mentor.intern_ids.ids)
