from datetime import date
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestDiagnosis(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create test physician
        self.physician = self.env['hr.hospital.physician'].create({
            'name_first': 'Test',
            'name_last': 'Physician',
            'specialty': 'General Practice'
        })
        
        # Create test patient
        self.patient = self.env['hr.hospital.patient'].create({
            'name_first': 'Test',
            'name_last': 'Patient',
            'date_of_birth': date(1990, 1, 1)
        })
        
        # Create test disease category
        self.disease_category = self.env['hr.hospital.disease.category'].create({
            'name': 'Test Category'
        })
        
        # Create test disease
        self.disease = self.env['hr.hospital.disease'].create({
            'name': 'Test Disease',
            'category_id': self.disease_category.id
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
                'treatment_recommendations': ''  # Empty treatment recommendations
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
