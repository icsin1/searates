# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import TransactionCase, tagged, Form
from odoo.addons.freight_management_charges.tests.common import FreightShipmentCommon

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TariffCommon(FreightShipmentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Setup freight shipment basis data
        cls.setup_measurement_basis_data()
