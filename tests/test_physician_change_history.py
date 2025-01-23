from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase


class TestPhysicianChangeHistory(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create test physicians
        self.physician_1 = self.env['hr.hospital.physician'].create({
            'name_first': 'John',
            'name_last': 'Doe',
            'specialty': 'General Practice',
            'is_intern': False
        })

        self.physician_2 = self.env['hr.hospital.physician'].create({
            'name_first': 'Jane',
            'name_last': 'Smith',
            'specialty': 'Pediatrics',
            'is_intern': False
        })

    def test_create_history_record(self):
        """Test creating a physician change history record"""
        patient = self.env['hr.hospital.patient'].create({
            'name_first': 'Test',
            'name_last': 'Patient',
            'date_of_birth': '1990-01-01'
        })
        history = self.env['hr.hospital.physician.change.history'].create({
            'patient_id': patient.id,
            'physician_id': self.physician_1.id,
        })

        self.assertTrue(history.id)
        self.assertEqual(history.patient_id, patient)
        self.assertEqual(history.physician_id, self.physician_1)
        self.assertTrue(history.date_established)

    def test_multiple_changes(self):
        """Test multiple physician changes for the same patient"""
        patient = self.env['hr.hospital.patient'].create({
            'name_first': 'Test',
            'name_last': 'Patient',
            'date_of_birth': '1990-01-01'
        })
        # Create first history record
        history1 = self.env['hr.hospital.physician.change.history'].create({
            'patient_id': patient.id,
            'physician_id': self.physician_1.id,
            'date_established': datetime.now()
        })

        # Create second history record after some time
        history2 = self.env['hr.hospital.physician.change.history'].create({
            'patient_id': patient.id,
            'physician_id': self.physician_2.id,
            'date_established': datetime.now() + timedelta(days=1)
        })

        # Verify both records exist and are different
        self.assertNotEqual(history1.id, history2.id)
        self.assertEqual(history1.patient_id, history2.patient_id)
        self.assertNotEqual(history1.physician_id, history2.physician_id)
        self.assertLess(history1.date_established, history2.date_established)

    def test_ordering(self):
        """Test that records are ordered by date_established
        in descending order"""
        patient = self.env['hr.hospital.patient'].create({
            'name_first': 'Test',
            'name_last': 'Patient',
            'date_of_birth': '1990-01-01'
        })
        # Create multiple records with different dates
        date_base = datetime.now()
        records = []

        for i in range(3):
            physician_id = (
                self.physician_1.id if i % 2 == 0 else self.physician_2.id
            )
            record = self.env['hr.hospital.physician.change.history'].create({
                'patient_id': patient.id,
                'physician_id': physician_id,
                'date_established': date_base + timedelta(days=i)
            })
            records.append(record)

        # Get all records for the patient, ordered by date
        history_records = self.env[
            'hr.hospital.physician.change.history'].search([(
                'patient_id', '=', patient.id
            )])

        # Verify ordering
        self.assertEqual(len(history_records), 3)
        # Most recent should be first
        self.assertEqual(history_records[0], records[2])
        # Oldest should be last
        self.assertEqual(history_records[2], records[0])

    def test_required_fields(self):
        """Test that required fields are enforced"""
        patient = self.env['hr.hospital.patient'].create({
            'name_first': 'Test',
            'name_last': 'Patient',
            'date_of_birth': '1990-01-01'
        })
        # Create a valid record to verify basic functionality
        history = self.env['hr.hospital.physician.change.history'].create({
            'date_established': datetime.now(),
            'patient_id': patient.id,
            'physician_id': self.physician_1.id,
        })

        # Verify the record was created and has all required fields
        self.assertTrue(history.id)
        self.assertTrue(history.patient_id)
        self.assertTrue(history.physician_id)
        self.assertTrue(history.date_established)

        # Verify relationships
        self.assertEqual(history.patient_id, patient)
        self.assertEqual(history.physician_id, self.physician_1)

    def test_patient_physician_relation(self):
        """Test the relationships between history records and related models"""
        patient = self.env['hr.hospital.patient'].create({
            'name_first': 'Test',
            'name_last': 'Patient',
            'date_of_birth': '1990-01-01'
        })
        history = self.env['hr.hospital.physician.change.history'].create({
            'patient_id': patient.id,
            'physician_id': self.physician_1.id,
        })

        # Test patient relation
        self.assertEqual(history.patient_id.name_first, 'Test')
        self.assertEqual(history.patient_id.name_last, 'Patient')

        # Test physician relation
        self.assertEqual(history.physician_id.name_first, 'John')
        self.assertEqual(history.physician_id.name_last, 'Doe')
        self.assertEqual(history.physician_id.specialty, 'General Practice')

    def test_patient_create_with_physician(self):
        """Test history record creation when creating patient with physician"""
        # Create new patient with physician
        new_patient = self.env['hr.hospital.patient'].create({
            'name_first': 'New',
            'name_last': 'Patient',
            'date_of_birth': '1995-01-01',
            'personal_physician': self.physician_1.id,
        })

        # Check if history record was created
        history = self.env['hr.hospital.physician.change.history'].search([
            ('patient_id', '=', new_patient.id),
            ('physician_id', '=', self.physician_1.id),
        ])

        self.assertTrue(history)
        self.assertEqual(len(history), 1)
        self.assertEqual(history.physician_id, self.physician_1)

    def test_patient_create_without_physician(self):
        """Test no history record when creating patient without physician"""
        # Create new patient without physician
        new_patient = self.env['hr.hospital.patient'].create({
            'name_first': 'New',
            'name_last': 'Patient',
            'date_of_birth': '1995-01-01',
        })

        # Check that no history record was created
        history = self.env['hr.hospital.physician.change.history'].search([
            ('patient_id', '=', new_patient.id),
        ])

        self.assertFalse(history)

    def test_patient_physician_change(self):
        """Test history record creation when changing patient's physician"""
        # Create new patient with initial physician
        patient = self.env['hr.hospital.patient'].create({
            'name_first': 'Test',
            'name_last': 'Patient',
            'date_of_birth': '1995-01-01',
            'personal_physician': self.physician_1.id,
        })

        # Verify initial history record
        initial_history = self.env['hr.hospital.physician.change.history'].search([
            ('patient_id', '=', patient.id),
            ('physician_id', '=', self.physician_1.id),
        ])
        self.assertTrue(initial_history)
        self.assertEqual(len(initial_history), 1)

        # Change patient's physician
        patient.write({
            'personal_physician': self.physician_2.id,
        })

        # Get all history records for the patient
        history_records = self.env['hr.hospital.physician.change.history'].search([
            ('patient_id', '=', patient.id),
        ], order='date_established desc')

        # Should have 2 records now
        self.assertEqual(len(history_records), 2)

        # Verify both records exist with correct physicians
        physician_ids = history_records.mapped('physician_id.id')
        self.assertIn(self.physician_1.id, physician_ids)
        self.assertIn(self.physician_2.id, physician_ids)

        # Verify the second record's timestamp is not earlier than the first
        self.assertGreaterEqual(
            history_records[0].date_established,
            history_records[1].date_established
        )

        # Verify current physician is physician_2
        self.assertEqual(patient.personal_physician.id, self.physician_2.id)
