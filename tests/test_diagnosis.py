from datetime import date
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestDiagnosis(TransactionCase):
    def _create_person(self, model, values):
        """Helper method to create a person (patient or physician) with required fields."""
        default_values = {
            'name_first': 'Test',
            'name_last': 'Person',
            'gender': 'male',
            'phone': '1234567890',
            'email': 'test@example.com'
        }
        return self.env[model].create({**default_values, **values})

    def setUp(self):
        super().setUp()

        # Create test physician
        self.physician = self._create_person('hr.hospital.physician', {
            'name_first': 'Test',
            'name_last': 'Physician',
            'specialty': 'General Practice',
            'is_intern': False
        })

        # Create test patient
        self.patient = self._create_person('hr.hospital.patient', {
            'name_first': 'Test',
            'name_last': 'Patient',
            'date_of_birth': date(1990, 1, 1)
        })

        # Create test disease category
        self.disease_category = self.env[
            'hr.hospital.disease.category'
            ].create({'name': 'Test Category'})

        # Create test disease
        self.disease = self.env['hr.hospital.disease'].create({
            'name': 'Test Disease',
            'category_id': self.disease_category.id
        })

        # Create disease category and disease
        self.disease_category_2 = self.env[
            'hr.hospital.disease.category'
            ].create({'name': 'Test Category 2'})
        self.disease_2 = self.env['hr.hospital.disease'].create({
            'name': 'Test Disease 2',
            'category_id': self.disease_category_2.id})

        # Create mentor physician
        self.mentor = self._create_person('hr.hospital.physician', {
            'name_first': 'Senior',
            'name_last': 'Doctor',
            'specialty': 'Surgery',
            'is_intern': False
        })

        # Create test user for mentor
        self.mentor_user = self.env['res.users'].create({
            'name': 'Senior Doctor',
            'login': 'senior.doctor',
            'email': 'senior.doctor@test.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

        # Link mentor user to physician
        self.mentor.write({
            'user_id': self.mentor_user.id
        })

        # Create intern physician
        self.intern = self._create_person('hr.hospital.physician', {
            'name_first': 'Junior',
            'name_last': 'Doctor',
            'specialty': 'Surgery',
            'is_intern': True,
            'mentor_id': self.mentor.id
        })

        # Create regular physician
        self.physician_2 = self._create_person('hr.hospital.physician', {
            'name_first': 'Regular',
            'name_last': 'Doctor',
            'specialty': 'Surgery',
            'is_intern': False
        })

        # Create patient
        self.patient_2 = self._create_person('hr.hospital.patient', {
            'name_first': 'Test',
            'name_last': 'Patient 2',
            'date_of_birth': date(1990, 1, 1)
        })

    def test_create_diagnosis(self):
        """Test creating a new diagnosis record"""
        diagnosis = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': date.today(),
            'physician': self.physician.id,
            'patient_id': self.patient.id,
            'disease_id': self.disease.id,
            'treatment_recommendations': 'Test treatment'
        })

        self.assertTrue(diagnosis.id)
        self.assertEqual(diagnosis.physician.id, self.physician.id)
        self.assertEqual(diagnosis.patient_id.id, self.patient.id)
        self.assertEqual(diagnosis.disease_id.id, self.disease.id)
        self.assertEqual(diagnosis.treatment_recommendations, 'Test treatment')

    def test_empty_required_fields(self):
        """Test that required fields are enforced"""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.diagnosis'].create({
                'date_of_diagnosis': date.today(),
                'physician': self.physician.id,
                'patient_id': self.patient.id,
                'disease_id': self.disease.id,
                # Empty treatment recommendations
                'treatment_recommendations': ''
            })

    def test_empty_required_fields_2(self):
        """Test that required fields cannot be empty"""
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.diagnosis'].create({
                'date_of_diagnosis': '2025-01-20',
                'physician': self.physician_2.id,
                'patient_id': self.patient_2.id,
                'disease_id': self.disease_2.id,
                'treatment_recommendations': ''
            })

    def test_relations(self):
        """Test the relationships between diagnosis and related models"""
        diagnosis = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': date.today(),
            'physician': self.physician.id,
            'patient_id': self.patient.id,
            'disease_id': self.disease.id,
            'treatment_recommendations': 'Test treatment'
        })

        # Test physician relation
        self.assertEqual(diagnosis.physician.display_name, 'Test Physician')

        # Test patient relation
        self.assertEqual(diagnosis.patient_id.display_name, 'Test Patient')

        # Test disease relation
        self.assertEqual(diagnosis.disease_id.name, 'Test Disease')

    def test_regular_physician_diagnosis(self):
        """Test diagnosis creation by regular physician"""
        diagnosis = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': '2025-01-20',
            'physician': self.physician_2.id,
            'patient_id': self.patient.id,
            'disease_id': self.disease.id,
            'treatment_recommendations': 'Test treatment'
        })

        self.assertEqual(diagnosis.state, 'final')
        self.assertFalse(diagnosis.needs_mentor_review)

    def test_intern_diagnosis_workflow(self):
        """Test the complete workflow of an intern's diagnosis"""
        # Create diagnosis by intern
        diagnosis = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': '2025-01-20',
            'physician': self.intern.id,
            'patient_id': self.patient_2.id,
            'disease_id': self.disease_2.id,
            'treatment_recommendations': 'Test treatment'
        })

        # Check initial state
        self.assertEqual(diagnosis.state, 'draft')
        self.assertTrue(diagnosis.needs_mentor_review)

        # Submit for review (should work without mentor comment)
        diagnosis.action_submit_for_review()
        self.assertEqual(diagnosis.state, 'pending_review')

        # Try to review without mentor comment (should fail)
        diagnosis = diagnosis.with_user(self.mentor_user)
        with self.assertRaises(ValidationError):
            diagnosis.action_review()

        # Add mentor comment and review
        diagnosis.write({'mentor_comment': 'Looks good'})
        diagnosis.action_review()
        self.assertEqual(diagnosis.state, 'reviewed')

        # Finalize the diagnosis
        diagnosis.action_finalize()
        self.assertEqual(diagnosis.state, 'final')

    def test_mentor_required_comment(self):
        """Test that mentor comment is required for intern diagnoses"""
        # Create diagnosis by intern
        diagnosis = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': '2025-01-20',
            'physician': self.intern.id,
            'patient_id': self.patient.id,
            'disease_id': self.disease.id,
            'treatment_recommendations': 'Test treatment'
        })

        # Initial state should be draft
        self.assertEqual(diagnosis.state, 'draft')

        # Can submit for review without comment
        diagnosis.action_submit_for_review()
        self.assertEqual(diagnosis.state, 'pending_review')

        # Switch to mentor user and try to review without comment
        diagnosis = diagnosis.with_user(self.mentor_user)
        with self.assertRaises(ValidationError):
            diagnosis.action_review()

    def test_wrong_mentor_review(self):
        """Test that only the assigned mentor can review a diagnosis"""
        # Create another mentor
        another_mentor = self._create_person('hr.hospital.physician', {
            'name_first': 'Another',
            'name_last': 'Mentor',
            'specialty': 'Surgery',
            'is_intern': False
        })
        another_mentor_user = self.env['res.users'].create({
            'name': 'Another Mentor',
            'login': 'another.mentor',
            'email': 'another.mentor@test.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        another_mentor.write({'user_id': another_mentor_user.id})

        # Create diagnosis by intern
        diagnosis = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': '2025-01-20',
            'physician': self.intern.id,
            'patient_id': self.patient.id,
            'disease_id': self.disease.id,
            'treatment_recommendations': 'Test treatment'
        })

        diagnosis.action_submit_for_review()

        # Try to review with wrong mentor
        diagnosis = diagnosis.with_user(another_mentor_user)
        diagnosis.write({'mentor_comment': 'Wrong mentor comment'})

        with self.assertRaises(ValidationError):
            diagnosis.action_review()

    def test_non_intern_review_attempt(self):
        """Test that diagnoses by non-interns cannot be submitted for review"""
        diagnosis = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': '2025-01-20',
            'physician': self.physician_2.id,
            'patient_id': self.patient.id,
            'disease_id': self.disease.id,
            'treatment_recommendations': 'Test treatment'
        })

        with self.assertRaises(ValidationError):
            diagnosis.action_submit_for_review()

    def test_multiple_diagnoses_same_patient(self):
        """Test creating multiple diagnoses for the same patient"""
        # Create first diagnosis
        diagnosis1 = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': '2025-01-20',
            'physician': self.physician.id,
            'patient_id': self.patient.id,
            'disease_id': self.disease.id,
            'treatment_recommendations': 'First treatment'
        })

        # Create second diagnosis for same patient
        diagnosis2 = self.env['hr.hospital.diagnosis'].create({
            'date_of_diagnosis': '2025-01-21',
            'physician': self.physician_2.id,
            'patient_id': self.patient.id,
            'disease_id': self.disease_2.id,
            'treatment_recommendations': 'Second treatment'
        })

        self.assertTrue(diagnosis1.id)
        self.assertTrue(diagnosis2.id)
        self.assertEqual(diagnosis1.patient_id, diagnosis2.patient_id)
        self.assertNotEqual(diagnosis1.disease_id, diagnosis2.disease_id)
        self.assertNotEqual(
            diagnosis1.date_of_diagnosis, diagnosis2.date_of_diagnosis)
