"""
Unit tests validating SXEWSimulator against Joseph Kafumbila's SimSXEWCu v7.0 benchmark.
"""
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sim_sxew_cu import (
    CircuitConfiguration,
    OperatingParams,
    PLSFeed,
    SXEWSimulator,
)


class TestSXEWSimulator(unittest.TestCase):
    def setUp(self):
        self.feed = PLSFeed(flow_m3h=1000.0, cu_gl=2.5, fe3_gl=0.5, fe2_gl=2.0, mn_gl=4.0, acid_gl=5.0)
        self.params = OperatingParams()
        self.sim = SXEWSimulator(self.feed, self.params)

    def test_configuration_a1_baseline(self):
        """Verify 2Ex-1S Baseline without wash stage against Excel Fig 1 data."""
        res = self.sim.simulate(CircuitConfiguration.A1_2Ex1S)

        self.assertAlmostEqual(res.volume_percent_extractant, 10.116, delta=0.05)
        self.assertAlmostEqual(res.max_loading_gl, 4.939, delta=0.05)
        self.assertAlmostEqual(res.extraction_efficiency_percent, 93.115, delta=0.1)
        self.assertAlmostEqual(res.total_copper_production_th, 2.178, delta=0.05)
        self.assertAlmostEqual(res.global_copper_recovery_percent, 87.14, delta=0.1)
        self.assertAlmostEqual(res.number_of_commercial_cells, 37.74, delta=0.5)
        self.assertAlmostEqual(res.number_of_scavenger_cells, 7.97, delta=0.2)
        self.assertAlmostEqual(res.bleed_flow_m3h, 4.268, delta=0.1)
        self.assertAlmostEqual(res.fe_mn_ratio_spent, 2.513, delta=0.1)
        self.assertGreater(res.mn3_concentration_spent_gl, 0.5)

    def test_configuration_a2_recirculation(self):
        """Verify Recirculation to E1 increases copper global recovery."""
        res_a1 = self.sim.simulate(CircuitConfiguration.A1_2Ex1S)
        res_a2 = self.sim.simulate(CircuitConfiguration.A2_2Ex1S)

        self.assertGreater(res_a2.global_copper_recovery_percent, res_a1.global_copper_recovery_percent)
        self.assertAlmostEqual(res_a2.global_copper_recovery_percent, 91.086, delta=0.1)
        self.assertAlmostEqual(res_a2.total_copper_production_th, 2.277, delta=0.05)

    def test_configuration_b1_launder_wash(self):
        """Verify E1 Launder Wash reduces Mn3+ in spent electrolyte."""
        res = self.sim.simulate(CircuitConfiguration.B1_2Ex1S)

        self.assertAlmostEqual(res.manganese_wash_efficiency_percent, 85.29, delta=0.1)
        self.assertAlmostEqual(res.mno4_concentration_spent_gl, 0.0, delta=0.001)
        self.assertAlmostEqual(res.fe_mn_ratio_spent, 7.147, delta=0.1)
        self.assertAlmostEqual(res.cu_fe_ratio_loaded_organic, 481.8, delta=1.0)

    def test_configuration_c1_raw_water_wash(self):
        """Verify dedicated raw water wash stage performance."""
        res = self.sim.simulate(CircuitConfiguration.C1_2Ex1S)

        self.assertAlmostEqual(res.manganese_wash_efficiency_percent, 95.45, delta=0.1)
        self.assertAlmostEqual(res.fe_mn_ratio_spent, 23.05, delta=0.2)
        self.assertEqual(res.mno4_concentration_spent_gl, 0.0)

    def test_configuration_d1_acid_scrub(self):
        """Verify acidulated water wash scrubs 50% iron and raises Cu/Fe ratio."""
        res = self.sim.simulate(CircuitConfiguration.D1_2Ex1S)

        self.assertAlmostEqual(res.iron_scrubbing_efficiency_percent, 50.0, delta=0.1)
        self.assertAlmostEqual(res.cu_fe_ratio_loaded_organic, 959.0, delta=2.0)
        self.assertAlmostEqual(res.bleed_flow_m3h, 2.626, delta=0.1)

    def test_configuration_e1_diluted_ewb(self):
        """Verify Diluted EWB wash achieves highest Cu/Fe ratio > 1000."""
        res = self.sim.simulate(CircuitConfiguration.E1_2Ex1S)

        self.assertAlmostEqual(res.iron_scrubbing_efficiency_percent, 56.625, delta=0.2)
        self.assertGreater(res.cu_fe_ratio_loaded_organic, 1000.0)
        self.assertAlmostEqual(res.global_copper_recovery_percent, 89.699, delta=0.1)
        self.assertAlmostEqual(res.acid_consumption_ew_t_tcu, 0.414, delta=0.05)

    def test_scaling_with_flow_rate(self):
        """Verify proportional scaling when PLS flow rate doubles."""
        sim_1000 = SXEWSimulator(PLSFeed(flow_m3h=1000.0))
        sim_2000 = SXEWSimulator(PLSFeed(flow_m3h=2000.0))

        res_1000 = sim_1000.simulate(CircuitConfiguration.A1_2Ex1S)
        res_2000 = sim_2000.simulate(CircuitConfiguration.A1_2Ex1S)

        self.assertAlmostEqual(res_2000.total_copper_production_th, 2 * res_1000.total_copper_production_th, delta=0.01)
        self.assertAlmostEqual(res_2000.bleed_flow_m3h, 2 * res_1000.bleed_flow_m3h, delta=0.01)
        self.assertAlmostEqual(res_2000.number_of_commercial_cells, 2 * res_1000.number_of_commercial_cells, delta=0.1)


if __name__ == "__main__":
    unittest.main()
