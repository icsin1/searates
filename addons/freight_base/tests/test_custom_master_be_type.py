
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCustomMasterBeType(TransactionCase):

    def setUp(self):
        super(TestCustomMasterBeType, self).setUp()
        self.CustomMasterBeType = self.env['custom.master.be.type']

    def test_create_custom_master_be_type_unique_constraint(self):
        vals = {'name': 'Test Custom Master BE Type'}
        record1 = self.CustomMasterBeType.create(vals)
        self.assertEqual(record1.name, 'Test Custom Master BE Type')
        with self.assertRaises(ValidationError):
            record1.copy({'name': 'Test Custom Master BE Type'})
