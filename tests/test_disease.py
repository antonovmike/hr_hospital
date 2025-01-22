from psycopg2.errors import NotNullViolation, UniqueViolation
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestDisease(TransactionCase):
    def setUp(self):
        super().setUp()
        
        # Create test disease categories
        self.category_infectious = self.env['hr.hospital.disease.category'].create({
            'name': 'Infectious Diseases',
        })
        self.category_chronic = self.env['hr.hospital.disease.category'].create({
            'name': 'Chronic Diseases',
        })

        # Create test diseases
        self.disease_flu = self.env['hr.hospital.disease'].create({
            'name': 'Influenza',
            'category_id': self.category_infectious.id,
        })
        self.disease_diabetes = self.env['hr.hospital.disease'].create({
            'name': 'Type 2 Diabetes',
            'category_id': self.category_chronic.id,
        })

    def test_disease_creation(self):
        """Test basic disease creation"""
        disease = self.env['hr.hospital.disease'].create({
            'name': 'COVID-19',
            'category_id': self.category_infectious.id,
        })
        
        self.assertTrue(disease.id)
        self.assertEqual(disease.name, 'COVID-19')
        self.assertEqual(disease.category_id, self.category_infectious)

    def test_disease_category_creation(self):
        """Test disease category creation"""
        category = self.env['hr.hospital.disease.category'].create({
            'name': 'Respiratory Diseases',
        })
        
        self.assertTrue(category.id)
        self.assertEqual(category.name, 'Respiratory Diseases')
        self.assertEqual(len(category.disease_ids), 0)

    def test_disease_category_relation(self):
        """Test relationship between diseases and categories"""
        # Check diseases are properly linked to categories
        self.assertIn(self.disease_flu, self.category_infectious.disease_ids)
        self.assertIn(self.disease_diabetes, self.category_chronic.disease_ids)
        
        # Create new disease in category and verify relation
        new_disease = self.env['hr.hospital.disease'].create({
            'name': 'Tuberculosis',
            'category_id': self.category_infectious.id,
        })
        self.assertIn(new_disease, self.category_infectious.disease_ids)
        self.assertEqual(len(self.category_infectious.disease_ids), 2)

    def test_disease_name_required(self):
        """Test that disease name is required"""
        with self.assertRaises(NotNullViolation):
            self.env.cr.execute("""
                INSERT INTO hr_hospital_disease (category_id, create_uid, write_uid)
                VALUES (%s, %s, %s)
            """, [self.category_infectious.id, self.env.uid, self.env.uid])

    def test_disease_category_required(self):
        """Test that disease category is required"""
        with self.assertRaises(NotNullViolation):
            self.env.cr.execute("""
                INSERT INTO hr_hospital_disease (name, create_uid, write_uid)
                VALUES (%s, %s, %s)
            """, ['Test Disease', self.env.uid, self.env.uid])

    def test_category_name_required(self):
        """Test that category name is required"""
        with self.assertRaises(NotNullViolation):
            self.env.cr.execute("""
                INSERT INTO hr_hospital_disease_category (create_uid, write_uid)
                VALUES (%s, %s)
            """, [self.env.uid, self.env.uid])

    def test_disease_update(self):
        """Test disease record updates"""
        # Update disease name
        self.disease_flu.write({
            'name': 'Influenza Type A'
        })
        self.assertEqual(self.disease_flu.name, 'Influenza Type A')
        
        # Change disease category
        self.disease_flu.write({
            'category_id': self.category_chronic.id
        })
        self.assertEqual(self.disease_flu.category_id, self.category_chronic)
        self.assertIn(self.disease_flu, self.category_chronic.disease_ids)
        self.assertNotIn(self.disease_flu, self.category_infectious.disease_ids)

    def test_category_update(self):
        """Test category updates and impact on diseases"""
        # Update category name
        self.category_infectious.write({
            'name': 'Viral Diseases'
        })
        self.assertEqual(self.category_infectious.name, 'Viral Diseases')
        
        # Verify diseases still linked after category update
        self.assertIn(self.disease_flu, self.category_infectious.disease_ids)

    def test_disease_unique_name(self):
        """Test that disease names should be unique"""
        with self.assertRaises(UniqueViolation):
            self.env.cr.execute("""
                INSERT INTO hr_hospital_disease (name, category_id, create_uid, write_uid)
                VALUES (%s, %s, %s, %s)
            """, ['Influenza', self.category_chronic.id, self.env.uid, self.env.uid])

    def test_category_unique_name(self):
        """Test that category names should be unique"""
        with self.assertRaises(UniqueViolation):
            self.env.cr.execute("""
                INSERT INTO hr_hospital_disease_category (name, create_uid, write_uid)
                VALUES (%s, %s, %s)
            """, ['Infectious Diseases', self.env.uid, self.env.uid])
